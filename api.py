"""API web que expone el mismo pipeline que el asistente interactivo.

Es el backend de la landing page de React (carpeta web/): recibe la eleccion de
proveedores y el guion, corre la generacion en un hilo aparte y deja consultar
el progreso en vivo, el video final y su descarga.

Levantar con:

    python api.py            (o: uvicorn api:app --reload --port 8000)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from asistente import construir_orquestador
from videogen.config import settings
from videogen.models import Scene

BASE_DIR = Path(__file__).parent
REMOTION_DIR = BASE_DIR / "remotion"
WEB_DIST = BASE_DIR / "web" / "dist"

_RENDERED_RE = re.compile(r"(Rendered|Encoded)\s+(\d+)/(\d+)")

# ---------- Configuracion de despliegue ----------
# En local no hace falta tocar nada. En produccion, el front vive en Vercel y
# este backend en otro host, asi que hay que declarar de que origen se aceptan
# pedidos y (muy recomendado) poner una clave para que no cualquiera gaste los
# creditos de las APIs.

APP_TOKEN = os.getenv("APP_TOKEN") or None

_DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
ALLOWED_ORIGINS = [
    origen.strip() for origen in os.getenv("ALLOWED_ORIGINS", "").split(",") if origen.strip()
] or _DEV_ORIGINS

# Cada trabajo ocupa CPU, disco y creditos: limitamos cuantos corren a la vez.
MAX_JOBS_CONCURRENTES = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))


# ---------- Catalogo de proveedores ----------
# Cada opcion declara que API key necesita, para que la UI pueda avisar cuando
# falta configurarla en el .env en vez de fallar recien al generar.

PROVIDERS = {
    "visuals": [
        {"id": "pollinations", "label": "Pollinations", "cost": "gratis", "requires": None,
         "note": "Sin API key. Limite: 1 imagen cada ~45s, asi que tarda unos minutos."},
        {"id": "kieai", "label": "Kie.ai / Nano Banana", "cost": "pago", "requires": "KIEAI_API_KEY",
         "note": "La mejor calidad de imagen y la mas rapida."},
        {"id": "apify", "label": "Apify (fotos reales)", "cost": "pago", "requires": "APIFY_API_KEY",
         "note": "Fotos reales de Google Images. Ojo con los derechos de autor."},
    ],
    "voice": [
        {"id": "edge_tts", "label": "Edge TTS", "cost": "gratis", "requires": None,
         "note": "Voz neuronal es-AR. Sin API key."},
        {"id": "elevenlabs", "label": "ElevenLabs", "cost": "pago", "requires": "ELEVENLABS_API_KEY",
         "note": "Voz mas natural y expresiva. Requiere plan pago."},
    ],
    "music": [
        {"id": "none", "label": "Sin musica", "cost": "gratis", "requires": None, "note": None},
        {"id": "kieai", "label": "Kie.ai / Suno", "cost": "pago", "requires": "KIEAI_API_KEY",
         "note": "Compone una pista instrumental a medida."},
    ],
    "sfx": [
        {"id": "none", "label": "Sin efectos", "cost": "gratis", "requires": None, "note": None},
        {"id": "elevenlabs", "label": "ElevenLabs", "cost": "pago", "requires": "ELEVENLABS_API_KEY",
         "note": "Un efecto puntual por escena. Solo con guion propio."},
    ],
}

_KEYS = {
    "OPENROUTER_API_KEY": settings.openrouter_api_key,
    "ELEVENLABS_API_KEY": settings.elevenlabs_api_key,
    "KIEAI_API_KEY": settings.kieai_api_key,
    "APIFY_API_KEY": settings.apify_api_key,
    "GROQ_API_KEY": settings.groq_api_key,
}


# ---------- Modelos de la request ----------

class SceneInput(BaseModel):
    description: str = Field(min_length=1)
    duration_s: float = Field(default=4.0, gt=0)
    sfx_prompt: str | None = None
    overlay_text: str | None = None


class JobRequest(BaseModel):
    mode: Literal["prueba", "real"] = "prueba"
    topic: str = Field(min_length=1)
    script_source: Literal["ia", "yo"] = "ia"
    script: str | None = None
    scenes: list[SceneInput] = []
    visuals: str = "pollinations"
    voice: str = "edge_tts"
    energetic_voice: bool = False
    music: str = "none"
    music_mood: str = "upbeat modern pop, instrumental"
    sfx: str = "none"
    closing_text: str | None = None
    render: bool = True


# ---------- Estado de los trabajos ----------

@dataclass
class Job:
    id: str
    state: str = "running"  # running | done | error
    stage: str = "start"
    events: list[dict] = field(default_factory=list)
    project_id: str | None = None
    script_text: str | None = None
    scene_count: int = 0
    render_progress: float | None = None
    video_url: str | None = None
    error: str | None = None

    def log(self, stage: str, message: str) -> None:
        self.stage = stage
        self.events.append({"stage": stage, "message": message, "at": datetime.now().isoformat()})


JOBS: dict[str, Job] = {}
_JOBS_LOCK = threading.Lock()


def _render(job: Job, project_id: str) -> None:
    """Renderiza el MP4 con Remotion, reportando el avance en el job."""
    job.log("render", "Renderizando el MP4 con Remotion...")

    comando = (
        f"npx remotion render src/index.ts Video out/{project_id}.mp4 "
        f"--props=public/renders/{project_id}/props.json"
    )
    proceso = subprocess.Popen(
        comando,
        cwd=REMOTION_DIR,
        shell=True,  # en Windows npx se resuelve via shell
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    ultima_linea = ""
    for linea in proceso.stdout:  # type: ignore[union-attr]
        ultima_linea = linea.strip()
        match = _RENDERED_RE.search(linea)
        if match:
            hechos, total = int(match.group(2)), int(match.group(3))
            # Dos fases (render + encode) que reportamos como un solo 0-100.
            avance = hechos / total * 100
            job.render_progress = avance if match.group(1) == "Rendered" else avance
    proceso.wait()

    if proceso.returncode != 0:
        raise RuntimeError(f"Remotion fallo al renderizar. Ultima linea: {ultima_linea}")

    job.render_progress = 100.0
    job.video_url = f"/api/jobs/{job.id}/video"
    job.log("render", "Video renderizado")


def _run_job(job: Job, req: JobRequest) -> None:
    try:
        orquestador = construir_orquestador(
            req.mode,
            req.script_source,
            req.visuals,
            req.voice,
            req.energetic_voice,
            "mock" if req.mode == "prueba" and req.music != "none" else req.music,
            req.sfx if req.mode == "real" else "none",
        )

        guion = req.script if req.script_source == "yo" else None
        escenas = (
            [
                Scene(
                    index=i,
                    description=s.description,
                    duration_s=s.duration_s,
                    sfx_prompt=s.sfx_prompt or None,
                    overlay_text=s.overlay_text or None,
                )
                for i, s in enumerate(req.scenes)
            ]
            if req.script_source == "yo"
            else None
        )
        if req.script_source == "yo" and not (guion and escenas):
            raise ValueError("Con guion propio hay que mandar el texto y al menos una escena")

        proyecto = orquestador.run(
            req.topic,
            script_text=guion,
            scenes=escenas,
            closing_text=req.closing_text or None,
            music_mood=req.music_mood,
            on_event=job.log,
        )

        if proyecto.error:
            raise RuntimeError(proyecto.error)

        job.project_id = proyecto.id
        job.script_text = proyecto.script_text
        job.scene_count = len(proyecto.scenes)

        # Siempre dejamos el props.json listo, asi el comando de Remotion que
        # muestra la UI funciona aunque no se renderice ahora.
        props_path = REMOTION_DIR / "public" / "renders" / proyecto.id / "props.json"
        props_path.write_text(json.dumps({"projectId": proyecto.id}), encoding="utf-8")

        if req.render:
            _render(job, proyecto.id)

        job.state = "done"
        job.log("done", "Listo")

    except Exception as exc:  # noqa: BLE001 - se reporta al cliente via estado del job
        job.state = "error"
        job.error = str(exc)
        job.log("failed", str(exc))


# ---------- App ----------

app = FastAPI(title="Generar-Videos API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def requiere_token(
    x_app_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> None:
    """Si APP_TOKEN esta configurado, exige la clave.

    Se acepta por header (lo normal) o por query string, porque el <video> del
    navegador no puede mandar headers propios.
    """
    if APP_TOKEN is None:
        return
    if x_app_token != APP_TOKEN and token != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Clave de acceso invalida o faltante")


@app.get("/api/health")
def health() -> dict:
    """Publico: sirve para que el front sepa si hay que pedir la clave."""
    return {"ok": True, "auth_required": APP_TOKEN is not None}


@app.get("/api/providers", dependencies=[Depends(requiere_token)])
def get_providers() -> dict:
    """Catalogo de proveedores + que API keys estan configuradas en el .env."""
    return {
        "providers": PROVIDERS,
        "configured_keys": {name: bool(value) for name, value in _KEYS.items()},
    }


@app.post("/api/jobs", dependencies=[Depends(requiere_token)])
def create_job(req: JobRequest) -> dict:
    with _JOBS_LOCK:
        corriendo = sum(1 for j in JOBS.values() if j.state == "running")
        if corriendo >= MAX_JOBS_CONCURRENTES:
            raise HTTPException(
                status_code=429,
                detail=f"Ya hay {corriendo} videos generandose. Espera a que termine alguno.",
            )
        job = Job(id=uuid.uuid4().hex[:8])
        JOBS[job.id] = job
    threading.Thread(target=_run_job, args=(job, req), daemon=True).start()
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}", dependencies=[Depends(requiere_token)])
def get_job(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return {
        "id": job.id,
        "state": job.state,
        "stage": job.stage,
        "events": job.events,
        "project_id": job.project_id,
        "script_text": job.script_text,
        "scene_count": job.scene_count,
        "render_progress": job.render_progress,
        "video_url": job.video_url,
        "error": job.error,
    }


@app.get("/api/jobs/{job_id}/video", dependencies=[Depends(requiere_token)])
def get_job_video(job_id: str):
    job = JOBS.get(job_id)
    if job is None or not job.project_id:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    path = REMOTION_DIR / "out" / f"{job.project_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="El video todavia no esta renderizado")
    return FileResponse(path, media_type="video/mp4", filename=f"{job.project_id}.mp4")


# La landing page compilada (web/dist) se sirve desde la misma app, si existe.
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    # En produccion el host inyecta PORT y hay que escuchar en 0.0.0.0.
    puerto = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
    uvicorn.run(app, host=host, port=puerto)

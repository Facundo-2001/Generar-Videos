"""Asistente interactivo: te hace preguntas en la terminal (guion, imagenes,
voz, musica, efectos y escenas), genera todas las piezas del video y, si
queres, lo renderiza en MP4 con Remotion. Todo en un solo comando:

    python asistente.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from main import (
    _build_music_provider,
    _build_sfx_provider,
    _build_visual_provider,
    _build_voice_provider,
)
from videogen.config import settings
from videogen.models import Scene
from videogen.orchestrator import VideoOrchestrator

REMOTION_DIR = Path(__file__).parent / "remotion"


# ---------- Ayudas para preguntar ----------

def preguntar(texto: str, por_defecto: str = "") -> str:
    """Pide un texto. Si el usuario aprieta Enter sin escribir, usa el valor por defecto."""
    sufijo = f" [{por_defecto}]" if por_defecto else ""
    while True:
        respuesta = input(f"{texto}{sufijo}: ").strip()
        if respuesta:
            return respuesta
        if por_defecto:
            return por_defecto
        print("  Escribi algo para continuar.")


def elegir(texto: str, opciones: dict[str, str], por_defecto: str) -> str:
    """Muestra un menu numerado y devuelve la clave de la opcion elegida."""
    print(f"\n{texto}")
    claves = list(opciones)
    for numero, clave in enumerate(claves, start=1):
        marca = "  (por defecto)" if clave == por_defecto else ""
        print(f"  {numero}. {opciones[clave]}{marca}")
    while True:
        respuesta = input("Elegi un numero (Enter = por defecto): ").strip()
        if not respuesta:
            return por_defecto
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(claves):
            return claves[int(respuesta) - 1]
        print(f"  Escribi un numero del 1 al {len(claves)}.")


def preguntar_numero(texto: str, por_defecto: float) -> float:
    while True:
        respuesta = input(f"{texto} [{por_defecto}]: ").strip().replace(",", ".")
        if not respuesta:
            return por_defecto
        try:
            valor = float(respuesta)
            if valor > 0:
                return valor
        except ValueError:
            pass
        print("  Escribi un numero mayor a 0 (por ejemplo 4 o 3.5).")


def si_o_no(texto: str, por_defecto: bool = False) -> bool:
    opciones = "S/n" if por_defecto else "s/N"
    respuesta = input(f"{texto} ({opciones}): ").strip().lower()
    if not respuesta:
        return por_defecto
    return respuesta in ("s", "si", "sí", "y", "yes")


# ---------- Preguntas del video ----------

def preguntar_escenas(con_efectos: bool) -> list[Scene]:
    cantidad = int(preguntar_numero("\n¿Cuantas escenas (imagenes) queres?", 4))
    print("Tip: describi las imagenes en INGLES, los generadores de imagenes las entienden mejor.")
    escenas = []
    for i in range(cantidad):
        print(f"\n--- Escena {i + 1} de {cantidad} ---")
        descripcion = preguntar("Descripcion de la imagen")
        duracion = preguntar_numero("Duracion en segundos", 4)
        efecto = None
        if con_efectos:
            efecto = input("Efecto de sonido (en ingles, Enter = ninguno): ").strip() or None
        escenas.append(Scene(index=i, description=descripcion, duration_s=duracion, sfx_prompt=efecto))
    return escenas


def main() -> None:
    print("=" * 50)
    print("  Asistente para generar videos tipo Reels")
    print("=" * 50)

    modo = elegir(
        "¿En que modo queres trabajar?",
        {"prueba": "Prueba (gratis, datos falsos, para probar que todo anda)", "real": "Real (usa las APIs)"},
        por_defecto="prueba",
    )

    # 1. Guion
    tema = preguntar("\nTema del video")
    origen_guion = elegir(
        "¿Quien escribe el guion?",
        {"ia": "La IA (OpenRouter), a partir del tema", "yo": "Yo lo escribo"},
        por_defecto="ia",
    )

    # 2. Proveedores
    if modo == "real":
        imagenes = elegir(
            "¿Con que se generan las imagenes?",
            {"pollinations": "Pollinations (gratis)", "kieai": "Kie.ai / Nano Banana (pago)", "apify": "Apify, fotos reales de Google (pago)"},
            por_defecto="pollinations",
        )
        voz = elegir(
            "¿Que voz en off usamos?",
            {"edge_tts": "Edge TTS (gratis)", "elevenlabs": "ElevenLabs (pago)"},
            por_defecto="edge_tts",
        )
        voz_energica = voz == "edge_tts" and si_o_no("¿Voz rapida y animada, tipo vendedor?")
        musica = elegir(
            "¿Musica de fondo?",
            {"none": "Sin musica", "kieai": "Kie.ai / Suno (pago)"},
            por_defecto="none",
        )
        efectos = elegir(
            "¿Efectos de sonido por escena?",
            {"none": "Sin efectos", "elevenlabs": "ElevenLabs (pago)"},
            por_defecto="none",
        )
    else:
        imagenes = voz = "mock"
        voz_energica = False
        musica = "mock" if si_o_no("\n¿Probar tambien la musica de fondo?") else "none"
        efectos = "none"

    estilo_musica = "neutral"
    if musica != "none":
        estilo_musica = preguntar("Estilo de la musica (en ingles)", "upbeat modern pop, instrumental")

    # 3. Escenas (solo si el guion lo escribe el usuario; si no, las arma la IA)
    guion = escenas = None
    if origen_guion == "yo":
        print("\nEscribi el texto que va a decir la voz en off (todo en una linea).")
        guion = preguntar("Guion")
        escenas = preguntar_escenas(con_efectos=efectos != "none")
    elif efectos != "none":
        print("\nAviso: cuando la IA escribe el guion, las escenas no traen efectos de sonido.")
        print("Si queres efectos, elegi escribir el guion vos.")

    cierre = input("\nTexto de cierre al final del video (ej: shinkastudio.dev, Enter = ninguno): ").strip() or None

    # 4. Armar el orquestador con lo elegido
    orquestador = construir_orquestador(modo, origen_guion, imagenes, voz, voz_energica, musica, efectos)

    # 5. Generar
    print("\nGenerando las piezas del video... (puede tardar unos minutos)")
    proyecto = orquestador.run(
        tema,
        script_text=guion,
        scenes=escenas,
        closing_text=cierre,
        music_mood=estilo_musica,
    )
    if proyecto.error:
        print(f"\n❌ Fallo en el estado '{proyecto.status.value}': {proyecto.error}")
        sys.exit(1)

    print(f"\n✅ Listo. ID del proyecto: {proyecto.id}")
    print(f"   Guion: {proyecto.script_text}")
    print(f"   Escenas: {len(proyecto.scenes)}")

    # 6. Renderizar con Remotion
    (REMOTION_DIR / "props.json").write_text(json.dumps({"projectId": proyecto.id}), encoding="utf-8")
    if si_o_no("\n¿Renderizar ahora el MP4 con Remotion?", por_defecto=True):
        renderizar(proyecto.id)
    else:
        print("\nPara renderizarlo despues:")
        print("  cd remotion")
        print(f"  npx remotion render src/index.ts Video out/{proyecto.id}.mp4 --props=props.json")


def construir_orquestador(modo, origen_guion, imagenes, voz, voz_energica, musica, efectos) -> VideoOrchestrator:
    if modo == "prueba":
        from videogen.providers.mock import (
            MockMusicProvider,
            MockScriptProvider,
            MockSubtitleProvider,
            MockVisualProvider,
            MockVoiceProvider,
        )

        return VideoOrchestrator(
            script_provider=MockScriptProvider(),
            visual_provider=MockVisualProvider(),
            voice_provider=MockVoiceProvider(),
            music_provider=MockMusicProvider() if musica == "mock" else None,
            subtitle_provider=MockSubtitleProvider(),
            output_root=settings.output_dir,
        )

    from videogen.providers.text_timing_subtitles import TextTimingSubtitleProvider

    script_provider = None
    if origen_guion == "ia":
        from videogen.providers.openrouter_script import OpenRouterScriptProvider

        if not settings.openrouter_api_key:
            raise SystemExit("Falta OPENROUTER_API_KEY en .env (la necesita la IA que escribe el guion).")
        script_provider = OpenRouterScriptProvider(api_key=settings.openrouter_api_key, model=settings.openrouter_model)

    return VideoOrchestrator(
        script_provider=script_provider,
        visual_provider=_build_visual_provider(imagenes),
        voice_provider=_build_voice_provider(voz, energetic=voz_energica),
        music_provider=_build_music_provider(musica),
        sfx_provider=_build_sfx_provider(efectos),
        subtitle_provider=TextTimingSubtitleProvider(),
        output_root=settings.output_dir,
    )


def renderizar(project_id: str) -> None:
    salida = f"out/{project_id}.mp4"
    comando = f"npx remotion render src/index.ts Video {salida} --props=props.json"
    print(f"\nRenderizando: {comando}\n")
    # shell=True para que Windows encuentre npx
    resultado = subprocess.run(comando, cwd=REMOTION_DIR, shell=True)
    if resultado.returncode == 0:
        print(f"\n🎬 Video listo en: remotion/{salida}")
    else:
        print("\n❌ Remotion no pudo renderizar. Revisa el error de arriba.")
        print("   ¿Corriste 'npm install' dentro de la carpeta remotion?")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelado.")

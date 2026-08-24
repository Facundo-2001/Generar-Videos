"""Musica de fondo instrumental via Kie.ai (Suno)."""

from __future__ import annotations

import time
from pathlib import Path

import requests

from videogen.providers.base import MusicProvider

_CREATE_URL = "https://api.kie.ai/api/v1/generate"
_STATUS_URL = "https://api.kie.ai/api/v1/generate/record-info"
_POLL_INTERVAL_S = 8
_MAX_POLLS = 40


class KieAiMusicProvider(MusicProvider):
    def __init__(self, api_key: str, model: str = "V4_5") -> None:
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self.model = model

    def generate_music(self, mood: str, duration_s: float, output_dir: Path) -> Path:
        create_resp = requests.post(
            _CREATE_URL,
            headers=self.headers,
            json={
                "customMode": True,
                "instrumental": True,
                "style": mood,
                "title": "Background Track",
                "model": self.model,
                # Requerido por la API aunque no lo usemos: hacemos polling en vez
                # de esperar el webhook.
                "callBackUrl": "https://example.com/kieai-callback",
            },
            timeout=60,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json()
        if create_data.get("code") != 200:
            raise RuntimeError(f"Kie.ai (Suno) createTask fallo: {create_data}")
        task_id = create_data["data"]["taskId"]

        for _ in range(_MAX_POLLS):
            time.sleep(_POLL_INTERVAL_S)
            status_resp = requests.get(
                _STATUS_URL, headers=self.headers, params={"taskId": task_id}, timeout=30
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()["data"]

            suno_data = (status_data.get("response") or {}).get("sunoData") or []
            audio_url = suno_data[0].get("audioUrl") if suno_data else None
            if audio_url:
                audio_bytes = requests.get(audio_url, timeout=120).content
                path = output_dir / "music.mp3"
                path.write_bytes(audio_bytes)
                return path

            status = (status_data.get("status") or "").upper()
            if "FAIL" in status or "ERROR" in status:
                raise RuntimeError(f"Kie.ai (Suno) no pudo generar la musica: {status_data}")

        raise RuntimeError("Kie.ai (Suno) no genero la musica a tiempo (timeout)")

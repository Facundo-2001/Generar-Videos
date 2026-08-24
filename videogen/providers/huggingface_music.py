"""Musica de fondo via la Inference API de Hugging Face (MusicGen)."""

from __future__ import annotations

import time
from pathlib import Path

import requests

from videogen.providers.base import MusicProvider

_API_URL = "https://api-inference.huggingface.co/models/{model}"
_MAX_RETRIES = 5
_RETRY_WAIT_S = 15


class HuggingFaceMusicProvider(MusicProvider):
    def __init__(self, api_key: str, model: str = "facebook/musicgen-small") -> None:
        self.api_key = api_key
        self.model = model

    def generate_music(self, mood: str, duration_s: float, output_dir: Path) -> Path:
        url = _API_URL.format(model=self.model)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": (
                f"instrumental background music, {mood} mood, no vocals, "
                "suitable as background for a short social media video"
            )
        }

        for attempt in range(_MAX_RETRIES):
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            if response.status_code == 200:
                path = output_dir / "music.wav"
                path.write_bytes(response.content)
                return path
            if response.status_code == 503 and attempt < _MAX_RETRIES - 1:
                # El modelo esta "despertando" en el servidor de Hugging Face.
                time.sleep(_RETRY_WAIT_S)
                continue
            response.raise_for_status()

        raise RuntimeError("Hugging Face no genero musica tras varios reintentos")

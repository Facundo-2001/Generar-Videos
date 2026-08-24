"""Generacion de imagenes por escena via el endpoint de imagenes de OpenRouter.

Usa la misma API key que el guion, pero un endpoint dedicado (/v1/images) que
factura contra los creditos de OpenRouter en vez de depender del billing de
Google directamente.
"""

from __future__ import annotations

import base64
from pathlib import Path

import requests

from videogen.models import Scene
from videogen.providers.base import VisualProvider

_IMAGES_URL = "https://openrouter.ai/api/v1/images"


class OpenRouterVisualProvider(VisualProvider):
    def __init__(self, api_key: str, model: str = "google/gemini-2.5-flash-image") -> None:
        self.api_key = api_key
        self.model = model

    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        response = requests.post(
            _IMAGES_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "prompt": scene.description,
                "aspect_ratio": "9:16",
            },
            timeout=120,
        )
        response.raise_for_status()
        image_data = response.json()["data"][0]["b64_json"]

        path = output_dir / f"scene_{scene.index}.png"
        path.write_bytes(base64.b64decode(image_data))
        return path

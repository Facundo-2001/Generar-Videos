"""Generacion de imagenes por escena via Pollinations.ai: no requiere API key."""

from __future__ import annotations

import urllib.parse
from pathlib import Path

import requests

from videogen.models import Scene
from videogen.providers.base import VisualProvider

_BASE_URL = "https://image.pollinations.ai/prompt/{prompt}"


class PollinationsVisualProvider(VisualProvider):
    def __init__(self, width: int = 1080, height: int = 1920) -> None:
        self.width = width
        self.height = height

    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        encoded_prompt = urllib.parse.quote(scene.description)
        url = _BASE_URL.format(prompt=encoded_prompt)
        response = requests.get(
            url,
            params={"width": self.width, "height": self.height, "nologo": "true"},
            timeout=120,
        )
        response.raise_for_status()

        path = output_dir / f"scene_{scene.index}.png"
        path.write_bytes(response.content)
        return path

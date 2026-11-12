"""Generacion de imagenes por escena via Pollinations.ai: no requiere API key.

El tier anonimo esta limitado a 1 imagen cada ~45 segundos por IP. Cuando se
pasa de ese limite la API devuelve 402 (o 429) con un JSON que indica cuantos
segundos faltan, asi que reintentamos esperando ese tiempo en vez de abortar la
generacion entera en la segunda escena.
"""

from __future__ import annotations

import re
import time
import urllib.parse
from pathlib import Path

import requests

from videogen.models import Scene
from videogen.providers.base import VisualProvider

_BASE_URL = "https://image.pollinations.ai/prompt/{prompt}"
_RATE_LIMIT_CODES = {402, 429}
_MAX_RETRIES = 6
_DEFAULT_WAIT_S = 45.0
_RETRY_AFTER_RE = re.compile(r"Retry after (\d+)s", re.IGNORECASE)


def _wait_seconds(response: requests.Response) -> float:
    """Segundos a esperar segun la respuesta (header Retry-After o el mensaje del body)."""
    header = response.headers.get("Retry-After")
    if header and header.strip().isdigit():
        return float(header.strip())

    match = _RETRY_AFTER_RE.search(response.text)
    if match:
        return float(match.group(1))

    return _DEFAULT_WAIT_S


class PollinationsVisualProvider(VisualProvider):
    def __init__(self, width: int = 1080, height: int = 1920) -> None:
        self.width = width
        self.height = height

    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        encoded_prompt = urllib.parse.quote(scene.description)
        url = _BASE_URL.format(prompt=encoded_prompt)

        for attempt in range(_MAX_RETRIES):
            response = requests.get(
                url,
                params={"width": self.width, "height": self.height, "nologo": "true"},
                timeout=120,
            )

            if response.status_code in _RATE_LIMIT_CODES and attempt < _MAX_RETRIES - 1:
                wait_s = _wait_seconds(response) + 2.0  # margen, el limite es por IP
                print(
                    f"  [pollinations] limite del tier gratuito en la escena {scene.index}: "
                    f"esperando {wait_s:.0f}s y reintentando..."
                )
                time.sleep(wait_s)
                continue

            response.raise_for_status()

            path = output_dir / f"scene_{scene.index}.png"
            path.write_bytes(response.content)
            return path

        raise RuntimeError(
            f"Pollinations rechazo la escena {scene.index} tras {_MAX_RETRIES} intentos "
            "(limite del tier gratuito: 1 imagen cada ~45s por IP)"
        )

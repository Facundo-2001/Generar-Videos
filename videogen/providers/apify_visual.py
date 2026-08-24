"""Busca fotos reales (no generadas por IA) en Google Images via un actor de Apify.

Ojo: las imagenes que devuelve son de terceros, con sus propios derechos de
autor. No son libres de uso comercial solo por aparecer en la busqueda; para un
video de marketing real conviene filtrar por licencia o usar un banco de fotos
con licencia clara en vez de esto.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import requests
from apify_client import ApifyClient
from PIL import Image

from videogen.models import Scene
from videogen.providers.base import VisualProvider

_ACTOR_ID = "hooli/google-images-scraper"


class ApifyImageSearchProvider(VisualProvider):
    def __init__(self, api_key: str, results_per_query: int = 5) -> None:
        self.client = ApifyClient(api_key)
        self.results_per_query = results_per_query

    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        run = self.client.actor(_ACTOR_ID).call(
            run_input={"queries": [scene.description], "maxResultsPerQuery": self.results_per_query}
        )
        items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items:
            raise RuntimeError(f"Apify no encontro imagenes para: {scene.description}")

        for item in items:
            url = item.get("imageUrl")
            if not url:
                continue
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()
                image = Image.open(BytesIO(resp.content)).convert("RGB")
            except Exception:  # noqa: BLE001 - probamos el siguiente resultado
                continue

            path = output_dir / f"scene_{scene.index}.png"
            image.save(path)
            return path

        raise RuntimeError(f"No se pudo descargar ninguna imagen para: {scene.description}")

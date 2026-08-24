"""Generacion de imagenes por escena via Kie.ai (modelos nano-banana / Gemini image)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from videogen.models import Scene
from videogen.providers.base import VisualProvider

_CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
_STATUS_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
_POLL_INTERVAL_S = 3
_MAX_POLLS = 60


class KieAiVisualProvider(VisualProvider):
    def __init__(self, api_key: str, model: str = "google/nano-banana") -> None:
        self.model = model
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        create_resp = requests.post(
            _CREATE_URL,
            headers=self.headers,
            json={
                "model": self.model,
                "input": {
                    "prompt": scene.description,
                    "output_format": "png",
                    "aspect_ratio": "9:16",
                    "image_size": "9:16",
                },
            },
            timeout=60,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json()
        if create_data.get("code") != 200:
            raise RuntimeError(f"Kie.ai createTask fallo: {create_data}")
        task_id = create_data["data"]["taskId"]

        for _ in range(_MAX_POLLS):
            time.sleep(_POLL_INTERVAL_S)
            status_resp = requests.get(
                _STATUS_URL, headers=self.headers, params={"taskId": task_id}, timeout=30
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()["data"]
            state = status_data.get("state")

            if state == "success":
                result = json.loads(status_data["resultJson"])
                image_url = result["resultUrls"][0]
                image_bytes = requests.get(image_url, timeout=60).content
                path = output_dir / f"scene_{scene.index}.png"
                path.write_bytes(image_bytes)
                return path

            if state == "fail":
                raise RuntimeError(f"Kie.ai no pudo generar la imagen: {status_data}")

        raise RuntimeError("Kie.ai no genero la imagen a tiempo (timeout)")

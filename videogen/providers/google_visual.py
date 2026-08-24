"""Generacion de imagenes por escena via Google AI (Gemini image generation).

Se genera una imagen fija por escena en vez de un video por escena: Veo
(generacion de video real) es async, tarda minutos por clip y tiene cuotas
mucho mas ajustadas que la generacion de imagenes. El approach usual para
Reels/TikTok con IA es armar el video final animando estas imagenes
(paneo/zoom) en la etapa de render, no generar video crudo por escena.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

from videogen.models import Scene
from videogen.providers.base import VisualProvider


class GoogleVisualProvider(VisualProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-image") -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        response = self.client.models.generate_content(
            model=self.model,
            contents=[scene.description],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="9:16"),
            ),
        )

        path = output_dir / f"scene_{scene.index}.png"
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                Image.open(BytesIO(part.inline_data.data)).save(path)
                return path

        raise RuntimeError(f"Google AI no devolvio ninguna imagen para la escena {scene.index}")

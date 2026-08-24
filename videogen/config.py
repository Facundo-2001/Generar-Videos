"""Configuracion del proyecto: API keys y rutas, cargadas desde variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "remotion/public/renders"))

    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    openrouter_image_model: str = os.getenv("OPENROUTER_IMAGE_MODEL", "google/gemini-2.5-flash-image")

    elevenlabs_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str | None = os.getenv("ELEVENLABS_VOICE_ID") or None

    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

    kieai_api_key: str | None = os.getenv("KIEAI_API_KEY")
    kieai_model: str = os.getenv("KIEAI_MODEL", "google/nano-banana")

    apify_api_key: str | None = os.getenv("APIFY_API_KEY")

    huggingface_api_key: str | None = os.getenv("HUGGINGFACE_API_KEY")
    huggingface_music_model: str = os.getenv("HUGGINGFACE_MUSIC_MODEL", "facebook/musicgen-small")


settings = Settings()

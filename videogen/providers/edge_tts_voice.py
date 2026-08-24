"""Texto a voz via edge-tts (voces neuronales de Microsoft Edge, gratis, sin API key)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from videogen.providers.base import VoiceProvider

DEFAULT_VOICE = "es-AR-TomasNeural"
DEFAULT_RATE = "+0%"
DEFAULT_PITCH = "+0Hz"

# Voz mas animada, tipo vendedor/comerciante enerigico: mismo idioma/region,
# pero mas rapida y con el tono un poco mas alto.
ENERGETIC_VOICE = "es-MX-JorgeNeural"
ENERGETIC_RATE = "+18%"
ENERGETIC_PITCH = "+6Hz"


class EdgeTTSVoiceProvider(VoiceProvider):
    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE,
        pitch: str = DEFAULT_PITCH,
    ) -> None:
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    def generate_voice(self, text: str, output_dir: Path) -> Path:
        path = output_dir / "voice.mp3"
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
        asyncio.run(communicate.save(str(path)))
        return path

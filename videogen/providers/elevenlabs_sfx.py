"""Efectos de sonido puntuales via ElevenLabs (requiere plan pago, ej. Starter)."""

from __future__ import annotations

from pathlib import Path

from elevenlabs import ElevenLabs

from videogen.providers.base import SoundEffectProvider


class ElevenLabsSoundEffectProvider(SoundEffectProvider):
    def __init__(self, api_key: str) -> None:
        self.client = ElevenLabs(api_key=api_key)

    def generate_sound_effect(self, description: str, duration_s: float, output_path: Path) -> Path:
        audio = self.client.text_to_sound_effects.convert(
            text=description,
            duration_seconds=max(0.5, min(duration_s, 22.0)),
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return output_path

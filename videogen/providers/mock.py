"""Implementaciones falsas de cada proveedor, para validar el pipeline end-to-end
(incluyendo el render final) sin llamar APIs reales ni gastar creditos."""

from __future__ import annotations

import wave
from pathlib import Path

from PIL import Image

from videogen.models import Scene
from videogen.providers.base import (
    MusicProvider,
    ScriptProvider,
    SubtitleProvider,
    VisualProvider,
    VoiceProvider,
)

_SCENE_COLORS = [(200, 80, 80), (80, 160, 200), (120, 200, 120), (200, 180, 80), (160, 100, 200)]


def _write_silent_wav(path: Path, duration_s: float, sample_rate: int = 44100) -> None:
    n_frames = int(duration_s * sample_rate)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * n_frames)


class MockScriptProvider(ScriptProvider):
    def generate_script(self, topic: str) -> tuple[str, list[Scene]]:
        script_text = f"Guion de ejemplo sobre: {topic}"
        scenes = [
            Scene(index=0, description=f"Introduccion a {topic}", duration_s=3.0),
            Scene(index=1, description=f"Desarrollo de {topic}", duration_s=4.0),
            Scene(index=2, description=f"Cierre sobre {topic}", duration_s=3.0),
        ]
        return script_text, scenes


class MockVisualProvider(VisualProvider):
    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        path = output_dir / f"scene_{scene.index}.png"
        color = _SCENE_COLORS[scene.index % len(_SCENE_COLORS)]
        Image.new("RGB", (1080, 1920), color).save(path)
        return path


class MockVoiceProvider(VoiceProvider):
    def generate_voice(self, text: str, output_dir: Path) -> Path:
        path = output_dir / "voice.wav"
        _write_silent_wav(path, duration_s=10.0)
        return path


class MockMusicProvider(MusicProvider):
    def generate_music(self, mood: str, duration_s: float, output_dir: Path) -> Path:
        path = output_dir / "music.wav"
        _write_silent_wav(path, duration_s=duration_s)
        return path


class MockSubtitleProvider(SubtitleProvider):
    def generate_subtitles(self, audio_path: Path, text: str, output_dir: Path) -> Path:
        path = output_dir / "subtitles.srt"
        path.write_text(
            "1\n00:00:00,000 --> 00:00:03,000\n" + text + "\n",
            encoding="utf-8",
        )
        return path

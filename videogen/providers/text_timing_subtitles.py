"""Subtitulos (.srt) generados a partir del texto real del guion, con tiempos
estimados por proporcion de caracteres en vez de transcribir el audio.

Evita errores de reconocimiento de voz en nombres propios/marca (ej. un ASR
transcribiendo mal "ShinkaStudio.dev"): el texto que se muestra es siempre
exactamente el que se le paso al VoiceProvider.
"""

from __future__ import annotations

import re
from pathlib import Path

from moviepy import AudioFileClip

from videogen.providers.base import SubtitleProvider

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _format_timestamp(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    millis = round((secs - int(secs)) * 1000)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(secs):02d},{millis:03d}"


class TextTimingSubtitleProvider(SubtitleProvider):
    def generate_subtitles(self, audio_path: Path, text: str, output_dir: Path) -> Path:
        duration = AudioFileClip(str(audio_path)).duration
        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]
        total_chars = sum(len(s) for s in sentences) or 1

        lines: list[str] = []
        t = 0.0
        for i, sentence in enumerate(sentences, start=1):
            chunk_duration = duration * len(sentence) / total_chars
            lines.append(str(i))
            lines.append(f"{_format_timestamp(t)} --> {_format_timestamp(t + chunk_duration)}")
            lines.append(sentence)
            lines.append("")
            t += chunk_duration

        path = output_dir / "subtitles.srt"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

"""Subtitulos (.srt) via Groq, transcribiendo el audio de voz con Whisper."""

from __future__ import annotations

from pathlib import Path

from groq import Groq

from videogen.providers.base import SubtitleProvider


def _format_timestamp(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    millis = round((secs - int(secs)) * 1000)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(secs):02d},{millis:03d}"


class GroqSubtitleProvider(SubtitleProvider):
    def __init__(self, api_key: str, model: str = "whisper-large-v3-turbo", language: str = "es") -> None:
        self.client = Groq(api_key=api_key)
        self.model = model
        self.language = language

    def generate_subtitles(self, audio_path: Path, text: str, output_dir: Path) -> Path:
        with open(audio_path, "rb") as f:
            transcription = self.client.audio.transcriptions.create(
                file=f,
                model=self.model,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                language=self.language,
            )

        lines: list[str] = []
        for i, segment in enumerate(transcription.segments, start=1):
            start = segment["start"] if isinstance(segment, dict) else segment.start
            end = segment["end"] if isinstance(segment, dict) else segment.end
            text = segment["text"] if isinstance(segment, dict) else segment.text
            lines.append(str(i))
            lines.append(f"{_format_timestamp(start)} --> {_format_timestamp(end)}")
            lines.append(text.strip())
            lines.append("")

        path = output_dir / "subtitles.srt"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

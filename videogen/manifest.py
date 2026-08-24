"""Genera manifest.json: describe el video (escenas, timing, subtitulos, texto
de cierre) para que el proyecto Remotion lo componga y renderice, en vez de
armar el mp4 final con moviepy desde Python."""

from __future__ import annotations

import json
import re
from pathlib import Path

from videogen.models import VideoProject

_SRT_BLOCK_RE = re.compile(
    r"\d+\s*\n"
    r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*\n"
    r"(.+?)(?=\n\n|\Z)",
    re.DOTALL,
)


def _srt_timestamp_to_s(ts: str) -> float:
    hms, millis = ts.split(",")
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(millis) / 1000


def _parse_srt(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8")
    return [
        {
            "start": _srt_timestamp_to_s(m.group(1)),
            "end": _srt_timestamp_to_s(m.group(2)),
            "text": m.group(3).strip().replace("\n", " "),
        }
        for m in _SRT_BLOCK_RE.finditer(content)
    ]


def write_manifest(
    project: VideoProject,
    project_dir: Path,
    voice_duration_s: float,
    closing_text: str | None = None,
    closing_subtitle: str | None = None,
    closing_text_seconds: float = 5.0,
    closing_color: str | None = None,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    # Las duraciones de escena del guion son solo una referencia: reescalamos
    # proporcionalmente para que la suma cubra exactamente la voz completa.
    planned_total = sum(scene.duration_s for scene in project.scenes) or 1.0
    scale = voice_duration_s / planned_total

    scenes = []
    t = 0.0
    for scene in project.scenes:
        duration = scene.duration_s * scale
        scenes.append(
            {
                "image": scene.visual_path.name,
                "start": t,
                "duration": duration,
                "highlight": scene.highlight,
                "sfx": scene.sfx_path.name if scene.sfx_path else None,
            }
        )
        t += duration

    manifest = {
        "fps": fps,
        "width": width,
        "height": height,
        "voiceSrc": project.voice_path.name,
        "musicSrc": project.music_path.name if project.music_path else None,
        "scenes": scenes,
        "subtitles": _parse_srt(project.subtitles_path) if project.subtitles_path else [],
        "closingText": closing_text,
        "closingSubtitle": closing_subtitle,
        "closingTextSeconds": closing_text_seconds,
        "closingColor": closing_color,
    }

    path = project_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

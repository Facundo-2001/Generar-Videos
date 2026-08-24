"""Modelos de datos que representan el estado de un video a lo largo del pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    PENDING = "pending"
    SCRIPT_READY = "script_ready"
    VISUALS_READY = "visuals_ready"
    VOICE_READY = "voice_ready"
    MUSIC_READY = "music_ready"
    SUBTITLES_READY = "subtitles_ready"
    MANIFEST_READY = "manifest_ready"
    RENDERED = "rendered"
    FAILED = "failed"


@dataclass
class Scene:
    index: int
    description: str
    duration_s: float
    visual_path: Path | None = None
    highlight: bool = False
    sfx_prompt: str | None = None
    sfx_path: Path | None = None


@dataclass
class VideoProject:
    id: str
    topic: str
    status: Status = Status.PENDING
    script_text: str = ""
    scenes: list[Scene] = field(default_factory=list)
    voice_path: Path | None = None
    music_path: Path | None = None
    subtitles_path: Path | None = None
    manifest_path: Path | None = None
    output_path: Path | None = None
    error: str | None = None

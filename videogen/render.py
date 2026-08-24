"""Ensambla el video final: escenas (imagenes) + voz + musica + subtitulos quemados."""

from __future__ import annotations

import re
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)
from moviepy.audio.fx import AudioLoop
from moviepy.video.fx import FadeIn

from videogen.models import VideoProject

VIDEO_SIZE = (1080, 1920)  # 9:16, vertical para Reels/TikTok
MUSIC_VOLUME = 0.15
SUBTITLE_FONT = "C:/Windows/Fonts/arialbd.ttf"
CLOSING_TEXT_SECONDS = 5.0
CLOSING_TEXT_COLOR = "#4DE8FF"
CLOSING_TEXT_STROKE = "#00344a"

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


def _parse_srt(path: Path) -> list[tuple[float, float, str]]:
    content = path.read_text(encoding="utf-8")
    return [
        (_srt_timestamp_to_s(m.group(1)), _srt_timestamp_to_s(m.group(2)), m.group(3).strip().replace("\n", " "))
        for m in _SRT_BLOCK_RE.finditer(content)
    ]


def _build_scene_clip(visual_path: Path, duration_s: float):
    clip = ImageClip(str(visual_path)).with_duration(duration_s).resized(height=VIDEO_SIZE[1])
    if clip.w > VIDEO_SIZE[0]:
        clip = clip.cropped(x_center=clip.w / 2, width=VIDEO_SIZE[0])
    return clip


def render_video(project: VideoProject, output_dir: Path, closing_text: str | None = None) -> Path:
    voice = AudioFileClip(str(project.voice_path))

    # Las duraciones de escena que estima el guion son solo una referencia: la
    # duracion real depende de como narra la voz. Reescalamos cada escena
    # proporcionalmente para que la suma cubra exactamente la voz completa;
    # si no, el video se queda sin imagenes (pantalla negra) mientras la voz
    # sigue hablando.
    planned_total = sum(scene.duration_s for scene in project.scenes) or 1.0
    scale = voice.duration / planned_total
    scene_clips = [
        _build_scene_clip(scene.visual_path, scene.duration_s * scale) for scene in project.scenes
    ]
    video = concatenate_videoclips(scene_clips, method="compose")

    audio_tracks = [voice]
    if project.music_path:
        music = AudioFileClip(str(project.music_path)).with_volume_scaled(MUSIC_VOLUME)
        music = music.with_effects([AudioLoop(duration=voice.duration)])
        audio_tracks.append(music)
    video = video.with_audio(CompositeAudioClip(audio_tracks))

    subtitle_clips = []
    if project.subtitles_path:
        for start, end, text in _parse_srt(project.subtitles_path):
            end = min(end, video.duration)
            if end <= start:
                continue
            txt = (
                TextClip(
                    font=SUBTITLE_FONT,
                    text=text,
                    font_size=64,
                    color="white",
                    stroke_color="black",
                    stroke_width=3,
                    size=(int(VIDEO_SIZE[0] * 0.9), None),
                    method="caption",
                    text_align="center",
                )
                .with_start(start)
                .with_duration(end - start)
                .with_position(("center", VIDEO_SIZE[1] * 0.75))
            )
            subtitle_clips.append(txt)

    closing_clips = []
    if closing_text:
        start = max(0.0, video.duration - CLOSING_TEXT_SECONDS)
        card_duration = video.duration - start
        dim = (
            ColorClip(size=VIDEO_SIZE, color=(0, 0, 0))
            .with_opacity(0.55)
            .with_start(start)
            .with_duration(card_duration)
        )
        title = (
            TextClip(
                font=SUBTITLE_FONT,
                text=closing_text,
                font_size=90,
                color=CLOSING_TEXT_COLOR,
                stroke_color=CLOSING_TEXT_STROKE,
                stroke_width=4,
                size=(int(VIDEO_SIZE[0] * 0.85), None),
                method="caption",
                text_align="center",
            )
            .with_start(start)
            .with_duration(card_duration)
            .with_position("center")
            .with_effects([FadeIn(0.6)])
        )
        closing_clips = [dim, title]

    final = CompositeVideoClip([video, *subtitle_clips, *closing_clips], size=VIDEO_SIZE)

    output_path = output_dir / "final_video.mp4"
    final.write_videofile(str(output_path), fps=30, codec="libx264", audio_codec="aac", logger=None)
    return output_path

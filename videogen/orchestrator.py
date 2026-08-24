"""Orquestador central: recibe un topic y coordina a los 5 proveedores de IA
para producir un VideoProject completo, actualizando el estado en cada paso."""

from __future__ import annotations

import uuid
from pathlib import Path

from moviepy import AudioFileClip

from videogen.manifest import write_manifest
from videogen.models import Scene, Status, VideoProject
from videogen.providers.base import (
    MusicProvider,
    ScriptProvider,
    SoundEffectProvider,
    SubtitleProvider,
    VisualProvider,
    VoiceProvider,
)


class VideoOrchestrator:
    def __init__(
        self,
        script_provider: ScriptProvider,
        visual_provider: VisualProvider,
        voice_provider: VoiceProvider,
        subtitle_provider: SubtitleProvider,
        output_root: Path,
        music_provider: MusicProvider | None = None,
        sfx_provider: SoundEffectProvider | None = None,
    ) -> None:
        self.script_provider = script_provider
        self.visual_provider = visual_provider
        self.voice_provider = voice_provider
        self.music_provider = music_provider
        self.sfx_provider = sfx_provider
        self.subtitle_provider = subtitle_provider
        self.output_root = output_root

    def run(
        self,
        topic: str,
        script_text: str | None = None,
        scenes: list[Scene] | None = None,
        closing_text: str | None = None,
        closing_subtitle: str | None = None,
        closing_text_seconds: float = 5.0,
        closing_color: str | None = None,
        music_mood: str = "neutral",
    ) -> VideoProject:
        """Si se pasan script_text y scenes, se usan tal cual (guion pre-escrito
        por el usuario) en vez de generarlos con el script_provider. closing_text,
        si se pasa, se superpone como tarjeta de cierre sobre los ultimos segundos
        del video (por ejemplo, el link del sitio); closing_color define su color
        (por defecto el cian de la tarjeta). music_mood se le pasa tal cual al
        proveedor de musica (estilo/genero/animo a componer)."""
        project = VideoProject(id=str(uuid.uuid4())[:8], topic=topic)
        project_dir = self.output_root / project.id
        project_dir.mkdir(parents=True, exist_ok=True)

        try:
            if script_text is not None and scenes is not None:
                project.script_text = script_text
                project.scenes = scenes
            else:
                project.script_text, project.scenes = self.script_provider.generate_script(topic)
            project.status = Status.SCRIPT_READY

            for scene in project.scenes:
                scene.visual_path = self.visual_provider.generate_visual(scene, project_dir)
            project.status = Status.VISUALS_READY

            if self.sfx_provider is not None:
                for scene in project.scenes:
                    if scene.sfx_prompt:
                        scene.sfx_path = self.sfx_provider.generate_sound_effect(
                            scene.sfx_prompt, duration_s=1.5, output_path=project_dir / f"sfx_{scene.index}.mp3"
                        )

            project.voice_path = self.voice_provider.generate_voice(project.script_text, project_dir)
            project.status = Status.VOICE_READY

            if self.music_provider is not None:
                total_duration = sum(scene.duration_s for scene in project.scenes)
                project.music_path = self.music_provider.generate_music(
                    mood=music_mood, duration_s=total_duration, output_dir=project_dir
                )
            project.status = Status.MUSIC_READY

            project.subtitles_path = self.subtitle_provider.generate_subtitles(
                project.voice_path, project.script_text, project_dir
            )
            project.status = Status.SUBTITLES_READY

            voice_duration = AudioFileClip(str(project.voice_path)).duration
            project.manifest_path = write_manifest(
                project,
                project_dir,
                voice_duration_s=voice_duration,
                closing_text=closing_text,
                closing_subtitle=closing_subtitle,
                closing_text_seconds=closing_text_seconds,
                closing_color=closing_color,
            )
            project.status = Status.MANIFEST_READY

        except Exception as exc:  # noqa: BLE001 - se registra y se re-expone en el estado
            project.status = Status.FAILED
            project.error = str(exc)

        return project

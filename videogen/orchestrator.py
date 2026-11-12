"""Orquestador central: recibe un topic y coordina a los 5 proveedores de IA
para producir un VideoProject completo, actualizando el estado en cada paso."""

from __future__ import annotations

import uuid
from collections.abc import Callable
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
        script_provider: ScriptProvider | None,
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
        on_event: Callable[[str, str], None] | None = None,
    ) -> VideoProject:
        """Si se pasan script_text y scenes, se usan tal cual (guion pre-escrito
        por el usuario) en vez de generarlos con el script_provider. closing_text,
        si se pasa, se superpone como tarjeta de cierre sobre los ultimos segundos
        del video (por ejemplo, el link del sitio); closing_color define su color
        (por defecto el cian de la tarjeta). music_mood se le pasa tal cual al
        proveedor de musica (estilo/genero/animo a componer). on_event, si se
        pasa, recibe (etapa, mensaje) en cada paso del pipeline: sirve para
        mostrar progreso en vivo (por ejemplo, en la UI web)."""
        project = VideoProject(id=str(uuid.uuid4())[:8], topic=topic)
        project_dir = self.output_root / project.id
        project_dir.mkdir(parents=True, exist_ok=True)

        def emit(stage: str, message: str) -> None:
            if on_event is not None:
                on_event(stage, message)

        try:
            emit("start", f"Proyecto {project.id} creado")
            if script_text is not None and scenes is not None:
                project.script_text = script_text
                project.scenes = scenes
                emit("script", f"Guion propio: {len(scenes)} escenas")
            elif self.script_provider is not None:
                emit("script", "Escribiendo el guion con la IA...")
                project.script_text, project.scenes = self.script_provider.generate_script(topic)
                emit("script", f"Guion listo: {len(project.scenes)} escenas")
            else:
                raise ValueError("Falta script_provider, o pasar script_text y scenes ya armados")
            project.status = Status.SCRIPT_READY

            total_scenes = len(project.scenes)
            for scene in project.scenes:
                emit("visuals", f"Generando imagen {scene.index + 1} de {total_scenes}...")
                scene.visual_path = self.visual_provider.generate_visual(scene, project_dir)
            project.status = Status.VISUALS_READY
            emit("visuals", f"{total_scenes} imagenes listas")

            if self.sfx_provider is not None:
                for scene in project.scenes:
                    if scene.sfx_prompt:
                        emit("sfx", f"Efecto de sonido de la escena {scene.index + 1}...")
                        scene.sfx_path = self.sfx_provider.generate_sound_effect(
                            scene.sfx_prompt, duration_s=1.5, output_path=project_dir / f"sfx_{scene.index}.mp3"
                        )

            emit("voice", "Grabando la voz en off...")
            project.voice_path = self.voice_provider.generate_voice(project.script_text, project_dir)
            project.status = Status.VOICE_READY
            emit("voice", "Voz lista")

            if self.music_provider is not None:
                total_duration = sum(scene.duration_s for scene in project.scenes)
                emit("music", "Componiendo la musica de fondo...")
                project.music_path = self.music_provider.generate_music(
                    mood=music_mood, duration_s=total_duration, output_dir=project_dir
                )
                emit("music", "Musica lista")
            project.status = Status.MUSIC_READY

            emit("subtitles", "Armando los subtitulos...")
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
            emit("manifest", "Manifest listo: el video se puede renderizar")

        except Exception as exc:  # noqa: BLE001 - se registra y se re-expone en el estado
            project.status = Status.FAILED
            project.error = str(exc)
            emit("failed", str(exc))

        return project

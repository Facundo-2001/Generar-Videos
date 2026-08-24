"""Punto de entrada: corre el pipeline con proveedores mock (por defecto, gratis)
o con los proveedores reales (--real, consume creditos de las APIs)."""

from __future__ import annotations

import argparse
import sys

from videogen.config import settings
from videogen.orchestrator import VideoOrchestrator
from videogen.providers.mock import (
    MockMusicProvider,
    MockScriptProvider,
    MockSubtitleProvider,
    MockVisualProvider,
    MockVoiceProvider,
)


def build_mock_orchestrator() -> VideoOrchestrator:
    return VideoOrchestrator(
        script_provider=MockScriptProvider(),
        visual_provider=MockVisualProvider(),
        voice_provider=MockVoiceProvider(),
        music_provider=MockMusicProvider(),
        subtitle_provider=MockSubtitleProvider(),
        output_root=settings.output_dir,
    )


def _build_visual_provider(name: str):
    if name == "pollinations":
        from videogen.providers.pollinations_visual import PollinationsVisualProvider

        return PollinationsVisualProvider()

    if name == "kieai":
        from videogen.providers.kieai_visual import KieAiVisualProvider

        if not settings.kieai_api_key:
            raise SystemExit("Falta KIEAI_API_KEY en .env")
        return KieAiVisualProvider(api_key=settings.kieai_api_key, model=settings.kieai_model)

    if name == "apify":
        from videogen.providers.apify_visual import ApifyImageSearchProvider

        if not settings.apify_api_key:
            raise SystemExit("Falta APIFY_API_KEY en .env")
        return ApifyImageSearchProvider(api_key=settings.apify_api_key)

    raise SystemExit(f"Proveedor de imagenes desconocido: {name}")


def _build_voice_provider(name: str, energetic: bool = False):
    if name == "edge_tts":
        from videogen.providers.edge_tts_voice import (
            ENERGETIC_PITCH,
            ENERGETIC_RATE,
            ENERGETIC_VOICE,
            EdgeTTSVoiceProvider,
        )

        if energetic:
            return EdgeTTSVoiceProvider(voice=ENERGETIC_VOICE, rate=ENERGETIC_RATE, pitch=ENERGETIC_PITCH)
        return EdgeTTSVoiceProvider()

    if name == "elevenlabs":
        from videogen.providers.elevenlabs_audio import ElevenLabsVoiceProvider

        if not settings.elevenlabs_api_key:
            raise SystemExit("Falta ELEVENLABS_API_KEY en .env")
        return ElevenLabsVoiceProvider(
            api_key=settings.elevenlabs_api_key, voice_id=settings.elevenlabs_voice_id
        )

    raise SystemExit(f"Proveedor de voz desconocido: {name}")


def _build_music_provider(name: str):
    if name == "none":
        return None

    if name == "kieai":
        from videogen.providers.kieai_music import KieAiMusicProvider

        if not settings.kieai_api_key:
            raise SystemExit("Falta KIEAI_API_KEY en .env")
        return KieAiMusicProvider(api_key=settings.kieai_api_key)

    raise SystemExit(f"Proveedor de musica desconocido: {name}")


def _build_sfx_provider(name: str):
    if name == "none":
        return None

    if name == "elevenlabs":
        from videogen.providers.elevenlabs_sfx import ElevenLabsSoundEffectProvider

        if not settings.elevenlabs_api_key:
            raise SystemExit("Falta ELEVENLABS_API_KEY en .env")
        return ElevenLabsSoundEffectProvider(api_key=settings.elevenlabs_api_key)

    raise SystemExit(f"Proveedor de efectos de sonido desconocido: {name}")


def build_real_orchestrator(
    visual_provider_name: str = "pollinations",
    voice_provider_name: str = "edge_tts",
    music_provider_name: str = "none",
    sfx_provider_name: str = "none",
    energetic_voice: bool = False,
) -> VideoOrchestrator:
    from videogen.providers.openrouter_script import OpenRouterScriptProvider
    from videogen.providers.text_timing_subtitles import TextTimingSubtitleProvider

    # Subtitulos: se generan a partir del texto real del guion (con tiempos
    # estimados) en vez de transcribir el audio con Groq, para evitar errores
    # de reconocimiento de voz en nombres propios/marca.
    missing = [
        name
        for name, value in [
            ("OPENROUTER_API_KEY", settings.openrouter_api_key),
        ]
        if not value
    ]
    if missing:
        raise SystemExit(f"Faltan variables de entorno en .env: {', '.join(missing)}")

    return VideoOrchestrator(
        script_provider=OpenRouterScriptProvider(
            api_key=settings.openrouter_api_key, model=settings.openrouter_model
        ),
        visual_provider=_build_visual_provider(visual_provider_name),
        voice_provider=_build_voice_provider(voice_provider_name, energetic=energetic_voice),
        music_provider=_build_music_provider(music_provider_name),
        sfx_provider=_build_sfx_provider(sfx_provider_name),
        subtitle_provider=TextTimingSubtitleProvider(),
        output_root=settings.output_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera un video a partir de un topic")
    parser.add_argument("topic", help="Tema del video a generar")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Usa los proveedores reales en vez de mocks",
    )
    parser.add_argument(
        "--visuals",
        choices=["pollinations", "kieai", "apify"],
        default="pollinations",
        help="Proveedor de imagenes: pollinations (gratis), kieai (nano-banana, pago) o apify (fotos reales de Google Images)",
    )
    parser.add_argument(
        "--voice",
        choices=["edge_tts", "elevenlabs"],
        default="edge_tts",
        help="Proveedor de voz: edge_tts (gratis) o elevenlabs (requiere plan pago para usar voces via API)",
    )
    parser.add_argument(
        "--energetic-voice",
        action="store_true",
        help="Con --voice edge_tts: usa una voz mas rapida y animada, tipo vendedor/comerciante",
    )
    parser.add_argument(
        "--music",
        choices=["none", "kieai"],
        default="none",
        help="Musica de fondo: none (sin musica) o kieai (Suno, pago)",
    )
    parser.add_argument(
        "--sfx",
        choices=["none", "elevenlabs"],
        default="none",
        help="Efectos de sonido puntuales por escena (requiere scene.sfx_prompt seteado en el guion)",
    )
    args = parser.parse_args()

    orchestrator = (
        build_real_orchestrator(args.visuals, args.voice, args.music, args.sfx, args.energetic_voice)
        if args.real
        else build_mock_orchestrator()
    )
    project = orchestrator.run(args.topic)

    print(f"Proyecto: {project.id}")
    print(f"Estado: {project.status}")
    if project.error:
        print(f"Error: {project.error}")
        sys.exit(1)

    print(f"Guion: {project.script_text}")
    print(f"Escenas: {len(project.scenes)}")
    print(f"Voz: {project.voice_path}")
    print(f"Musica: {project.music_path}")
    print(f"Subtitulos: {project.subtitles_path}")
    print(f"Manifest: {project.manifest_path}")
    print()
    print("Para previsualizar en Remotion Studio:")
    print(f'  cd remotion && npx remotion studio --props="{{\\"projectId\\":\\"{project.id}\\"}}"')


if __name__ == "__main__":
    main()

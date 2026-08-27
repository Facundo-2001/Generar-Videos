"""Genera un reel de marketing (Shinka Studio) a partir de un guion ya escrito
(texto + timing + texto en pantalla ya definidos por el usuario), en vez de
generarlo con un LLM. Usa imagenes de IA (conceptuales, sin una persona real
"actuando" a camara: eso queda inconsistente entre escenas), efectos de
sonido puntuales y musica de fondo, todo vía el mismo pipeline de videogen/.

No renderiza el mp4 final: al terminar imprime el comando de Remotion.
"""

from __future__ import annotations

import sys

from videogen.config import settings
from videogen.models import Scene
from videogen.orchestrator import VideoOrchestrator
from videogen.providers.elevenlabs_audio import (
    ENERGETIC_VOICE_SETTINGS,
    ElevenLabsVoiceProvider,
)
from videogen.providers.elevenlabs_sfx import ElevenLabsSoundEffectProvider
from videogen.providers.kieai_music import KieAiMusicProvider
from videogen.providers.kieai_visual import KieAiVisualProvider
from videogen.providers.text_timing_subtitles import TextTimingSubtitleProvider

VOICE_ID = "sm3Tj3nVXV4aDIrYlSZB"

MUSIC_MOOD = (
    "upbeat modern corporate pop, energetic and positive, motivational marketing background "
    "music, instrumental, no vocals, clean electronic beat, suitable for a social media ad "
    "about website design services"
)

SCENES = [
    Scene(
        index=0,
        description=(
            "Modern flat-lay advertising illustration of dollar bills and coins flying out of a "
            "small shop storefront window into the wind, dramatic warm lighting, business concept, "
            "high quality advertising photography style, vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=4.0,
        overlay_text="Estás perdiendo plata 💸",
        sfx_prompt="dramatic whoosh with a subtle cash register error buzz, short attention-grabbing sting",
    ),
    Scene(
        index=1,
        description=(
            "Close-up of a smartphone screen showing a bare minimal social media profile page next "
            "to a large greyed-out question mark icon, symbolizing doubt and distrust, clean modern "
            "advertising photography style, soft studio lighting, vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=8.0,
        overlay_text="Solo redes = Poca confianza",
        sfx_prompt="subtle uncertain notification ping, slightly tense short sound",
    ),
    Scene(
        index=2,
        description=(
            "Smartphone mockup displaying a sleek modern professional website with clean UI, glowing "
            "softly in a dark room at night suggesting it works while you sleep, warm blue and white "
            "glow, high quality product photography style, vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=8.0,
        overlay_text="Abierto 24/7 🌐",
        sfx_prompt="clean positive UI swoosh, bright modern chime, website loading sound",
    ),
    Scene(
        index=3,
        description=(
            "Bright modern laptop displaying an elegant website design on a clean desk, a glowing "
            "downward arrow icon and a chat message bubble icon floating nearby, energetic marketing "
            "advertisement style, vibrant colors, vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=6.0,
        overlay_text="Comentá WEB 👇",
        sfx_prompt="upbeat notification pop, short call-to-action click sound",
    ),
    Scene(
        index=4,
        description=(
            "Split-screen concept illustration: on one side a thriving glowing modern storefront with "
            "a website on a screen, on the other side a dim empty storefront losing customers walking "
            "away toward a competitor, dramatic contrast lighting, advertising concept art style, "
            "vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=4.0,
        overlay_text=None,
        sfx_prompt="soft dramatic heartbeat thump, short suspenseful accent",
    ),
]

SCRIPT_TEXT = " ".join(
    [
        "¿Sabías que estás perdiendo clientes al no tener un sitio web?",
        "Hoy en día, si alguien busca lo que hacés y solo encuentra tu Instagram, le generás dudas.",
        "Una web propia le da autoridad a tu negocio y, lo mejor de todo, está vendiendo por vos las 24 horas del día.",
        "En Shinka Studio creamos la plataforma que tu marca necesita para destacar. Mandanos un mensaje para empezar.",
        "No le regales más ventas a tu competencia. Por eso te pregunto...",
    ]
)


def build_orchestrator() -> VideoOrchestrator:
    missing = [
        name
        for name, value in [
            ("ELEVENLABS_API_KEY", settings.elevenlabs_api_key),
            ("KIEAI_API_KEY", settings.kieai_api_key),
        ]
        if not value
    ]
    if missing:
        raise SystemExit(f"Faltan variables de entorno en .env: {', '.join(missing)}")

    return VideoOrchestrator(
        script_provider=None,  # se pasa script_text/scenes ya armados
        visual_provider=KieAiVisualProvider(api_key=settings.kieai_api_key, model=settings.kieai_model),
        voice_provider=ElevenLabsVoiceProvider(
            api_key=settings.elevenlabs_api_key,
            voice_id=VOICE_ID,
            voice_settings=ENERGETIC_VOICE_SETTINGS,
        ),
        music_provider=KieAiMusicProvider(api_key=settings.kieai_api_key),
        sfx_provider=ElevenLabsSoundEffectProvider(api_key=settings.elevenlabs_api_key),
        subtitle_provider=TextTimingSubtitleProvider(),
        output_root=settings.output_dir,
    )


def main() -> None:
    orchestrator = build_orchestrator()
    project = orchestrator.run(
        "Shinka Studio - reel sitio web propio",
        script_text=SCRIPT_TEXT,
        scenes=SCENES,
        music_mood=MUSIC_MOOD,
    )

    print(f"Proyecto: {project.id}")
    print(f"Estado: {project.status}")
    if project.error:
        print(f"Error: {project.error}")
        sys.exit(1)

    print(f"Escenas: {len(project.scenes)}")
    print(f"Voz: {project.voice_path}")
    print(f"Musica: {project.music_path}")
    print(f"Subtitulos: {project.subtitles_path}")
    print(f"Manifest: {project.manifest_path}")
    print()
    print("Para renderizar el mp4 final:")
    print(f'  cd remotion && npx remotion render src/index.ts Video out/{project.id}.mp4 --props="{{\\"projectId\\":\\"{project.id}\\"}}"')


if __name__ == "__main__":
    main()

"""Genera el reel de marketing "beneficios de tu propia tienda online"
(Shinka Studio). El guion lo escribe este script directamente (no un LLM):
el usuario pidio puntos concretos (dashboard con estadisticas en tiempo real,
cero comisiones por no depender de una plataforma externa) y el resto de los
beneficios/CTA se completaron para llegar a ~60s con el mismo tono y voz que
el reel anterior. Imagenes conceptuales via Kie.ai, sfx puntuales via
ElevenLabs y musica de fondo via Kie.ai/Suno.

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
    "listing the benefits of having your own online store"
)

SCENES = [
    Scene(
        index=0,
        description=(
            "Vibrant modern online store front displayed on a laptop and smartphone side by side "
            "on a clean desk, colorful custom branding, energetic advertising photography style, "
            "vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=7.33,
        overlay_text="Beneficios de tu propia tienda 🛒",
        sfx_prompt="bright upbeat intro whoosh, positive attention-grabbing sting",
    ),
    Scene(
        index=1,
        description=(
            "Close-up of a sleek business dashboard interface on a large monitor, showing colorful "
            "real-time sales charts, graphs, revenue numbers and analytics widgets, glowing modern "
            "UI, professional product photography style, vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=8.79,
        overlay_text="Dashboard en tiempo real 📊",
        sfx_prompt="clean positive UI data blip sounds, modern tech chime",
    ),
    Scene(
        index=2,
        description=(
            "Advertising concept illustration of a full stack of glowing gold coins next to a large "
            "green checkmark and a bold '0%' commission symbol, a faded percentage sign dissolving "
            "away in the background, dramatic warm lighting, vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=11.72,
        overlay_text="0% comisiones por venta 💰",
        sfx_prompt="satisfying coin drop and positive cash register chime",
    ),
    Scene(
        index=3,
        description=(
            "Modern laptop displaying a fully custom branded online store with unique colors, logo "
            "and layout, a glowing shield icon floating beside it symbolizing security and "
            "independence from third parties, professional advertising photography style, vertical "
            "9:16 composition, no text or watermarks"
        ),
        duration_s=10.26,
        overlay_text="100% tuya, sin límites 🎨",
        sfx_prompt="soft positive whoosh transition, subtle shield lock click",
    ),
    Scene(
        index=4,
        description=(
            "Futuristic abstract illustration of glowing customer profile icons connected by data "
            "streams to a central online store icon, dark background with vibrant blue and purple "
            "glow, marketing technology concept art, vertical 9:16 composition, no text or watermarks"
        ),
        duration_s=7.69,
        overlay_text="Tus datos, tu estrategia 📈",
        sfx_prompt="soft futuristic data whoosh, subtle techy sparkle sound",
    ),
    Scene(
        index=5,
        description=(
            "Bright modern laptop and smartphone displaying an elegant custom online store design "
            "side by side on a clean desk, a glowing chat message bubble icon floating nearby, "
            "energetic marketing advertisement style, vibrant colors, vertical 9:16 composition, "
            "no text or watermarks"
        ),
        duration_s=12.45,
        overlay_text="Escribinos y empezá 🚀",
        sfx_prompt="upbeat notification pop, short call-to-action click sound",
    ),
]

SCRIPT_TEXT = " ".join(
    [
        "¿Sabías que tener tu propia tienda online puede cambiar completamente tu negocio? Te contamos algunos beneficios que quizás no conocías.",
        "Primero: un dashboard personalizado que te muestra las estadísticas de tu negocio en tiempo real, ventas, visitas y stock, todo en un solo lugar.",
        "Segundo: al no depender de una plataforma externa, no pagás comisiones por cada venta, porque la plataforma es cien por ciento tuya. Nada de porcentajes que se lleva Mercado Libre o Shopify.",
        "Tercero: tenés control total del diseño y la marca, sin límites impuestos por terceros ni riesgo de que te bajen la cuenta de un día para el otro.",
        "Y lo mejor de todo: los datos de tus clientes son tuyos, para armar tus propias estrategias de marketing y fidelización.",
        "En Shinka Studio te ayudamos a construir esa tienda, a tu medida, profesional y lista para vender desde el primer día. Mandanos un mensaje y empezá a quedarte con lo que siempre fue tuyo.",
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
        "Shinka Studio - reel beneficios tienda online propia",
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

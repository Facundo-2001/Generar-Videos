"""Genera un short (~60s) estilo ocultismo/conspiraciones: guion con gancho
rapido, voz grave e intrigante (ElevenLabs), imagenes oscuras/cinematicas
(Kie.ai) y musica dark ambient (Kie.ai/Suno).

Usa el mismo pipeline de videogen/ que main.py, pero con un guion, una voz y
un mood musical ajustados a este genero. No renderiza el mp4 final: al
terminar imprime el comando de Remotion para renderizarlo.
"""

from __future__ import annotations

import argparse
import sys

from videogen.config import settings
from videogen.orchestrator import VideoOrchestrator
from videogen.providers.elevenlabs_audio import (
    DARK_VOICE_ID,
    DARK_VOICE_SETTINGS,
    ElevenLabsVoiceProvider,
)
from videogen.providers.kieai_music import KieAiMusicProvider
from videogen.providers.kieai_visual import KieAiVisualProvider
from videogen.providers.openrouter_script import OpenRouterScriptProvider
from videogen.providers.text_timing_subtitles import TextTimingSubtitleProvider

OCCULT_PROMPT_TEMPLATE = """Escribi el guion de un short vertical (YouTube Shorts/TikTok/Reels, ~60 \
segundos de narracion hablada, entre 105 y 120 palabras -no mas- porque la voz narra pausada y \
grave) sobre el siguiente tema, con estilo canal de ocultismo / misterio / teorias conspirativas: \
{topic}

TONO Y ESTILO:
- Narrador serio, grave, pausado e intrigante, como un documental de misterios/conspiraciones. Nada \
de humor ni de tono publicitario/exclamativo.
- Encara el tema como leyenda/misterio/teoria a explorar ("cuentan que...", "quienes investigaron \
esto...", "hay quienes creen que...", "nunca se explico oficialmente..."), no como un hecho \
verificado ni como una acusacion directa contra personas reales identificables vivas. Evita \
afirmaciones medicas o politicas presentadas como hechos.
- Las primeras 1-2 frases son un GANCHO durisimo que atrapa en los primeros 3 segundos: una \
afirmacion perturbadora, una pregunta inquietante o la promesa de una revelacion prohibida. \
Prohibido arrancar con introducciones genericas tipo "hoy vamos a hablar de" o "en este video".
- Cerra con un giro, un dato final inquietante o una pregunta sin resolver que deje con ganas de mas \
(cliffhanger): el video tiene una tarjeta de "seguime para la parte 2" superpuesta en los ultimos \
segundos.

Dividi el guion en 7 a 9 escenas. Las primeras 2 escenas (el gancho) deben durar entre 2.5 y 3.5 \
segundos cada una para un corte rapido; el resto puede durar entre 5 y 8 segundos. La suma total \
debe rondar los 60 segundos.

Responde UNICAMENTE con JSON valido, sin texto adicional, con esta forma exacta:
{{
  "script": "texto completo del guion narrado en espanol, lo que dice la voz en off",
  "scenes": [
    {{"description": "visual description of the scene IN ENGLISH for an AI image generator: dark, \
moody, cinematic lighting, occult/conspiracy documentary aesthetic, ominous atmosphere, shadows, \
film grain, no text or watermarks, vertical 9:16 composition", "duration_s": 3.0}}
  ]
}}
"""

OCCULT_MUSIC_MOOD = (
    "dark ambient, ominous cinematic drone, mysterious and unsettling atmosphere, slow tempo, "
    "instrumental, no vocals, deep bass drones, distant eerie textures, suitable as background "
    "for an occult mystery documentary short"
)

OCCULT_CLOSING_COLOR = "#E8272E"
DEFAULT_CTA = "SEGUÍ PARA LA PARTE 2"


def build_occult_orchestrator() -> VideoOrchestrator:
    missing = [
        name
        for name, value in [
            ("OPENROUTER_API_KEY", settings.openrouter_api_key),
            ("ELEVENLABS_API_KEY", settings.elevenlabs_api_key),
            ("KIEAI_API_KEY", settings.kieai_api_key),
        ]
        if not value
    ]
    if missing:
        raise SystemExit(f"Faltan variables de entorno en .env: {', '.join(missing)}")

    return VideoOrchestrator(
        script_provider=OpenRouterScriptProvider(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            prompt_template=OCCULT_PROMPT_TEMPLATE,
        ),
        visual_provider=KieAiVisualProvider(api_key=settings.kieai_api_key, model=settings.kieai_model),
        voice_provider=ElevenLabsVoiceProvider(
            api_key=settings.elevenlabs_api_key,
            voice_id=DARK_VOICE_ID,
            voice_settings=DARK_VOICE_SETTINGS,
        ),
        music_provider=KieAiMusicProvider(api_key=settings.kieai_api_key),
        subtitle_provider=TextTimingSubtitleProvider(),
        output_root=settings.output_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera un short de ocultismo/conspiraciones a partir de un topic")
    parser.add_argument("topic", help="Tema del short a generar")
    parser.add_argument("--cta", default=DEFAULT_CTA, help="Texto de la tarjeta de cierre (vacio para omitirla)")
    parser.add_argument("--cta-subtitle", default=None, help="Subtitulo opcional debajo del CTA")
    args = parser.parse_args()

    orchestrator = build_occult_orchestrator()
    project = orchestrator.run(
        args.topic,
        closing_text=args.cta or None,
        closing_subtitle=args.cta_subtitle,
        closing_color=OCCULT_CLOSING_COLOR,
        music_mood=OCCULT_MUSIC_MOOD,
    )

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
    print("Para renderizar el mp4 final:")
    print(f'  cd remotion && npx remotion render src/index.ts Video out/{project.id}.mp4 --props="{{\\"projectId\\":\\"{project.id}\\"}}"')


if __name__ == "__main__":
    main()

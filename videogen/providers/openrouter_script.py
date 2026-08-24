"""Generacion de guion via OpenRouter (API compatible con OpenAI)."""

from __future__ import annotations

import json

from openai import OpenAI

from videogen.models import Scene
from videogen.providers.base import ScriptProvider

_PROMPT_TEMPLATE = """Escribi un guion corto para un video estilo Reels/TikTok \
(30 a 45 segundos de narracion) sobre el siguiente tema: {topic}

Dividi el guion en 3 a 5 escenas. Responde UNICAMENTE con JSON valido, sin \
texto adicional, con esta forma exacta:
{{
  "script": "texto completo del guion narrado en espanol, lo que dice la voz en off",
  "scenes": [
    {{"description": "visual description of the scene IN ENGLISH, for an AI image generator (los modelos de imagen entienden mejor ingles que espanol)", "duration_s": 4.0}}
  ]
}}
"""


class OpenRouterScriptProvider(ScriptProvider):
    def __init__(self, api_key: str, model: str, prompt_template: str = _PROMPT_TEMPLATE) -> None:
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self.model = model
        self.prompt_template = prompt_template

    def generate_script(self, topic: str) -> tuple[str, list[Scene]]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": self.prompt_template.format(topic=topic)}],
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)

        script_text = data["script"]
        scenes = [
            Scene(index=i, description=raw["description"], duration_s=float(raw["duration_s"]))
            for i, raw in enumerate(data["scenes"])
        ]
        return script_text, scenes

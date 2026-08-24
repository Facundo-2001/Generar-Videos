"""Interfaces comunes que debe implementar cada proveedor de IA.

Cada categoria (guion, visuales, voz, musica, subtitulos) define una interfaz
minima. Los proveedores reales (OpenAI, ElevenLabs, Runway, etc.) y los mocks
implementan estas mismas clases, por lo que el orquestador nunca sabe con que
proveedor concreto esta hablando.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from videogen.models import Scene


class ScriptProvider(ABC):
    @abstractmethod
    def generate_script(self, topic: str) -> tuple[str, list[Scene]]:
        """Devuelve el texto completo del guion y la lista de escenas derivadas."""


class VisualProvider(ABC):
    @abstractmethod
    def generate_visual(self, scene: Scene, output_dir: Path) -> Path:
        """Genera la imagen/video de una escena y devuelve la ruta del archivo."""


class VoiceProvider(ABC):
    @abstractmethod
    def generate_voice(self, text: str, output_dir: Path) -> Path:
        """Genera el audio de narracion y devuelve la ruta del archivo."""


class MusicProvider(ABC):
    @abstractmethod
    def generate_music(self, mood: str, duration_s: float, output_dir: Path) -> Path:
        """Genera musica/efectos de fondo y devuelve la ruta del archivo."""


class SubtitleProvider(ABC):
    @abstractmethod
    def generate_subtitles(self, audio_path: Path, text: str, output_dir: Path) -> Path:
        """Genera un archivo de subtitulos (.srt) y devuelve su ruta."""


class SoundEffectProvider(ABC):
    @abstractmethod
    def generate_sound_effect(self, description: str, duration_s: float, output_path: Path) -> Path:
        """Genera un efecto de sonido corto y puntual (no musica de fondo)."""

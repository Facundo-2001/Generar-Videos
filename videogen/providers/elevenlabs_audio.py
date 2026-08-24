"""Voz y musica de fondo via ElevenLabs."""

from __future__ import annotations

from pathlib import Path

from elevenlabs import ElevenLabs, VoiceSettings

from videogen.providers.base import MusicProvider, VoiceProvider

# Rachel, voz por defecto de ElevenLabs. Se puede sobreescribir con ELEVENLABS_VOICE_ID.
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Adam: voz masculina grave, el clasico "narrador de documental/misterio" de la
# libreria premade de ElevenLabs (funciona con la key actual, verificado con
# una llamada de prueba). Los settings bajan la velocidad y suben el "style"
# para una entrega mas pausada y dramatica, tipo canal de ocultismo/misterio.
DARK_VOICE_ID = "pNInz6obpgDQGcFmaJgB"
DARK_VOICE_SETTINGS = VoiceSettings(
    stability=0.45,
    similarity_boost=0.85,
    style=0.45,
    speed=0.90,
    use_speaker_boost=True,
)

_MIN_MUSIC_S = 10.0
_MAX_MUSIC_S = 300.0


class ElevenLabsVoiceProvider(VoiceProvider):
    def __init__(
        self,
        api_key: str,
        voice_id: str | None = None,
        voice_settings: VoiceSettings | None = None,
    ) -> None:
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id or DEFAULT_VOICE_ID
        self.voice_settings = voice_settings

    def generate_voice(self, text: str, output_dir: Path) -> Path:
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings=self.voice_settings,
        )
        path = output_dir / "voice.mp3"
        with open(path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return path


class ElevenLabsMusicProvider(MusicProvider):
    def __init__(self, api_key: str) -> None:
        self.client = ElevenLabs(api_key=api_key)

    def generate_music(self, mood: str, duration_s: float, output_dir: Path) -> Path:
        clamped_s = max(_MIN_MUSIC_S, min(duration_s, _MAX_MUSIC_S))
        audio = self.client.music.compose(
            prompt=(
                f"Musica de fondo instrumental, sin voz, estilo {mood}, "
                "apta como fondo de un video corto para redes sociales"
            ),
            music_length_ms=int(clamped_s * 1000),
            output_format="mp3_44100_128",
        )
        path = output_dir / "music.mp3"
        with open(path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return path

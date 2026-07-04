"""The friendly front desk for voice: `listen()` and `speak()`.

It bundles a speech-to-text engine and a text-to-speech engine together, and
knows how to build them from your settings.
"""

from __future__ import annotations

from nova.core.config import VoiceSettings
from nova.core.exceptions import ConfigError
from nova.core.logging import get_logger
from nova.voice.base import SpeechToText, TextToSpeech

logger = get_logger(__name__)


class VoiceManager:
    """Combines a listening engine and a speaking engine."""

    def __init__(self, stt: SpeechToText, tts: TextToSpeech) -> None:
        self.stt = stt
        self.tts = tts

    async def listen(self, audio: bytes) -> str:
        """Turn audio into text using the configured STT engine."""
        return await self.stt.transcribe(audio)

    async def speak(self, text: str) -> bytes:
        """Turn text into audio using the configured TTS engine."""
        return await self.tts.synthesize(text)


def _build_stt(engine: str) -> SpeechToText:
    if engine == "placeholder":
        from nova.voice.stt import PlaceholderSTT

        return PlaceholderSTT()
    raise ConfigError(f"Unknown speech-to-text engine '{engine}'. Valid: 'placeholder'.")


def _build_tts(engine: str) -> TextToSpeech:
    if engine == "placeholder":
        from nova.voice.tts import PlaceholderTTS

        return PlaceholderTTS()
    raise ConfigError(f"Unknown text-to-speech engine '{engine}'. Valid: 'placeholder'.")


def create_voice_manager(settings: VoiceSettings) -> VoiceManager:
    """Build a `VoiceManager` from the engine names in settings."""
    logger.info(
        "Voice: stt=%s, tts=%s", settings.stt_engine, settings.tts_engine
    )
    return VoiceManager(
        stt=_build_stt(settings.stt_engine.lower().strip()),
        tts=_build_tts(settings.tts_engine.lower().strip()),
    )

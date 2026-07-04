"""Placeholder speech-to-text (listening).

This does NOT actually recognize speech yet. It returns a clearly-labeled stub
so the rest of Nova can be built and tested. Swap this out for a real engine
(e.g. OpenAI Whisper) later — just make a class that follows `SpeechToText`.
"""

from __future__ import annotations

from nova.core.logging import get_logger
from nova.voice.base import SpeechToText

logger = get_logger(__name__)


class PlaceholderSTT(SpeechToText):
    """Fake transcriber: reports how much audio it 'heard' but recognizes nothing."""

    name = "placeholder"

    async def transcribe(self, audio: bytes) -> str:
        logger.warning(
            "Using PLACEHOLDER speech-to-text — no real recognition is happening."
        )
        return f"[placeholder transcription of {len(audio)} bytes of audio]"

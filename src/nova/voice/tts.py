"""Placeholder text-to-speech (speaking).

This does NOT produce real audio yet. It returns some labeled bytes so the app
works end-to-end. Swap this for a real engine (e.g. Piper) later — just make a
class that follows `TextToSpeech`.
"""

from __future__ import annotations

from nova.core.logging import get_logger
from nova.voice.base import TextToSpeech

logger = get_logger(__name__)


class PlaceholderTTS(TextToSpeech):
    """Fake speaker: returns placeholder bytes instead of real audio."""

    name = "placeholder"

    async def synthesize(self, text: str) -> bytes:
        logger.warning(
            "Using PLACEHOLDER text-to-speech — no real audio is being produced."
        )
        return f"[placeholder audio for: {text}]".encode()

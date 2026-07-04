"""The contracts for listening and speaking.

`SpeechToText` turns audio into words. `TextToSpeech` turns words into audio.
Real engines will implement these; for now we ship simple placeholders.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class SpeechToText(ABC):
    """Turns spoken audio into text (transcription)."""

    name: str = "base"

    @abstractmethod
    async def transcribe(self, audio: bytes) -> str:
        """Take raw audio bytes and return the recognized words."""
        raise NotImplementedError


class TextToSpeech(ABC):
    """Turns text into spoken audio."""

    name: str = "base"

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Take text and return audio bytes (e.g. WAV/MP3 data)."""
        raise NotImplementedError

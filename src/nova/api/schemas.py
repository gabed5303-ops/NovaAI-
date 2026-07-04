"""The "forms" for web requests and responses (what JSON goes in and comes out).

FastAPI uses these to validate incoming JSON and to document the API
automatically at /docs.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from nova.ai.schemas import Message


class ChatIn(BaseModel):
    """Input for POST /chat. Send EITHER `message` (simple) or `messages` (full)."""

    message: str | None = Field(default=None, description="A single user message (simplest).")
    messages: list[Message] | None = Field(
        default=None, description="A full conversation, if you need more control."
    )
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class ChatOut(BaseModel):
    """Output for POST /chat."""

    content: str
    model: str
    provider: str


class MemoryIn(BaseModel):
    """Input for POST /memory (save a memory)."""

    content: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class CommandRunIn(BaseModel):
    """Input for POST /commands/{name} (run a command)."""

    args: dict[str, Any] = Field(default_factory=dict)


class VoiceSpeakIn(BaseModel):
    """Input for POST /voice/tts (turn text into speech)."""

    text: str

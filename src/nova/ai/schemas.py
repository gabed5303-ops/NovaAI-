"""The "shapes" of the data we send to and get back from an AI brain.

Using these classes (instead of loose dictionaries) means Python checks the data
is correct for us, and editors can autocomplete the fields. Think of them as
clearly-labeled forms.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# A message's "role" says who is speaking:
#   system    = background instructions for the AI ("You are Nova, be helpful.")
#   user      = the human
#   assistant = the AI's own replies
Role = Literal["system", "user", "assistant"]


class Message(BaseModel):
    """One line in a conversation."""

    role: Role
    content: str


class ChatRequest(BaseModel):
    """Everything an AI brain needs to produce a reply."""

    messages: list[Message]
    # These are optional overrides. If left as None, the brain uses its defaults
    # from settings.
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class ChatResponse(BaseModel):
    """The AI brain's reply, plus a note about who produced it."""

    content: str = Field(description="The text the AI generated.")
    model: str = Field(description="Which model produced it, e.g. 'llama3'.")
    provider: str = Field(description="Which brain produced it, e.g. 'ollama'.")

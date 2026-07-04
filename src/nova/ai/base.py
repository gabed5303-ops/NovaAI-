"""The contract ("interface") every AI brain must follow.

`ABC` means "Abstract Base Class" — a template that can't be used directly.
Any real brain (Ollama, Anthropic, ...) must inherit from `LLMProvider` and
fill in the `chat` method. Because they all share this shape, the rest of Nova
can talk to "an AI brain" without caring which one it is.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from nova.ai.schemas import ChatRequest, ChatResponse


class LLMProvider(ABC):
    """Base template for an AI text-generating brain."""

    #: A short name for this brain, e.g. "ollama". Subclasses set this.
    name: str = "base"

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Take a conversation and return the AI's next reply.

        Must be implemented by every brain. Should raise
        `ProviderUnavailableError` if the brain can't be reached right now.
        """
        raise NotImplementedError

    async def health_check(self) -> bool:
        """Return True if the brain looks usable. Override for a real check.

        The default is optimistic (returns True) so brains that don't implement
        it still work.
        """
        return True

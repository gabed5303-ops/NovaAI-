"""The CLOUD AI brain: talks to Anthropic's Claude models.

This one needs two things:
  1. The `anthropic` library installed  ->  `uv sync --extra cloud`
  2. An API key set in the environment   ->  NOVA_AI__ANTHROPIC_API_KEY=sk-...

To keep the server able to start even when those aren't ready, we DON'T check
for them when Nova boots — we only check the moment someone actually tries to
chat. That way you get a clear message exactly when it matters.
"""

from __future__ import annotations

from typing import Any

from nova.ai.base import LLMProvider
from nova.ai.schemas import ChatRequest, ChatResponse
from nova.core.exceptions import ProviderUnavailableError
from nova.core.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Sends chat requests to Anthropic's Claude API."""

    name = "anthropic"

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client: Any = None  # Built lazily on first use (see _get_client).

    def _get_client(self) -> Any:
        """Create the Anthropic client on first use, with friendly errors."""
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise ProviderUnavailableError(
                "No Anthropic API key set. Set NOVA_AI__ANTHROPIC_API_KEY in your "
                "environment to use the Claude (cloud) brain."
            )
        try:
            import anthropic  # Imported here so Nova runs fine without it installed.
        except ImportError as exc:
            raise ProviderUnavailableError(
                "The 'anthropic' library isn't installed. Run: uv sync --extra cloud"
            ) from exc

        self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def chat(self, request: ChatRequest) -> ChatResponse:
        client = self._get_client()
        model = request.model or self.model

        # Anthropic keeps the "system" instructions separate from the back-and-forth
        # messages, so we split them out here.
        system_text = "\n".join(m.content for m in request.messages if m.role == "system")
        conversation = [
            {"role": m.role, "content": m.content}
            for m in request.messages
            if m.role != "system"
        ]

        try:
            message = await client.messages.create(
                model=model,
                system=system_text or None,
                messages=conversation,
                max_tokens=request.max_tokens or 1024,
                temperature=request.temperature if request.temperature is not None else 0.7,
            )
        except Exception as exc:  # noqa: BLE001 - wrap any API error in a clear one.
            raise ProviderUnavailableError(f"Anthropic request failed: {exc}") from exc

        # A reply can contain several "blocks"; we join the text ones together.
        text = "".join(
            getattr(block, "text", "")
            for block in message.content
            if getattr(block, "type", "") == "text"
        )
        return ChatResponse(content=text, model=model, provider=self.name)

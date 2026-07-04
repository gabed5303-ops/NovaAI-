"""The LOCAL AI brain: talks to Ollama running on your own computer.

Ollama (https://ollama.com) is a free app that runs AI models locally. It offers
a simple web address (default http://localhost:11434) we can send messages to.
This brain just forwards Nova's chat request there and reads back the reply.

If Ollama isn't running, we raise a clear `ProviderUnavailableError` instead of
a confusing crash.
"""

from __future__ import annotations

import httpx

from nova.ai.base import LLMProvider
from nova.ai.schemas import ChatRequest, ChatResponse
from nova.core.exceptions import ProviderUnavailableError
from nova.core.logging import get_logger

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """Sends chat requests to a local Ollama server."""

    name = "ollama"

    def __init__(self, host: str, model: str, timeout: float = 60.0) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or self.model
        # Build the tuning "options" separately so its type is clear.
        options: dict[str, object] = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,  # Ask for the whole reply at once (simpler for now).
            "options": options,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.host}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            # Covers "server not running", timeouts, bad status codes, etc.
            raise ProviderUnavailableError(
                f"Could not reach Ollama at {self.host}. Is it running? ({exc})"
            ) from exc

        data = response.json()
        content = data.get("message", {}).get("content", "")
        return ChatResponse(content=content, model=model, provider=self.name)

    async def health_check(self) -> bool:
        """Ping Ollama's version endpoint to see if it's up."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/version")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

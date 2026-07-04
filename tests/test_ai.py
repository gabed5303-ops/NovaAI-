"""Test that an unreachable AI brain fails cleanly (not with a confusing crash)."""

from __future__ import annotations

import pytest

from nova.ai.ollama_provider import OllamaProvider
from nova.ai.schemas import ChatRequest, Message
from nova.core.exceptions import ProviderUnavailableError


async def test_ollama_unreachable_raises_clear_error() -> None:
    # Port 1 has nothing listening, so the connection is refused immediately.
    provider = OllamaProvider(host="http://127.0.0.1:1", model="none", timeout=2)
    request = ChatRequest(messages=[Message(role="user", content="hi")])

    with pytest.raises(ProviderUnavailableError):
        await provider.chat(request)

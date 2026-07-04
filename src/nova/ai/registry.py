"""Picks the right AI brain based on your settings.

This is the ONE place that knows about every brain by name. Everywhere else in
Nova just says "give me the AI brain" and gets back something following the
`LLMProvider` contract. To add a new brain later, you only edit this file.
"""

from __future__ import annotations

from nova.ai.base import LLMProvider
from nova.core.config import AISettings
from nova.core.exceptions import ConfigError
from nova.core.logging import get_logger

logger = get_logger(__name__)


def create_provider(settings: AISettings) -> LLMProvider:
    """Build the AI brain named in `settings.provider`.

    Note: we import each brain only when it's chosen ("lazy import"), so Nova
    doesn't need every brain's optional dependencies installed to start.
    """
    provider = settings.provider.lower().strip()

    if provider == "ollama":
        from nova.ai.ollama_provider import OllamaProvider

        logger.info("Using local AI brain: Ollama (model=%s)", settings.ollama_model)
        return OllamaProvider(host=settings.ollama_host, model=settings.ollama_model)

    if provider == "anthropic":
        from nova.ai.anthropic_provider import AnthropicProvider

        logger.info("Using cloud AI brain: Anthropic (model=%s)", settings.anthropic_model)
        return AnthropicProvider(
            api_key=settings.anthropic_api_key, model=settings.anthropic_model
        )

    raise ConfigError(
        f"Unknown AI provider '{settings.provider}'. Valid options: 'ollama', 'anthropic'."
    )

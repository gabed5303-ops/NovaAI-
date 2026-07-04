"""The "control center" that builds and holds every part of Nova.

Instead of scattering global variables around, we build ONE `NovaContext` object
at startup. It holds the settings and every service (AI, memory, voice, commands,
events, plugins). We then pass this one object wherever it's needed — to plugins,
to the web routes, to tests. This keeps everything tidy and easy to test (a test
can build its own context with fake pieces).

This file is the single place where all the pieces get wired together.
"""

from __future__ import annotations

from dataclasses import dataclass

from nova.ai.base import LLMProvider
from nova.ai.registry import create_provider
from nova.commands.registry import CommandRegistry
from nova.core.config import Settings, load_settings
from nova.core.events import EventBus
from nova.core.logging import get_logger, setup_logging
from nova.memory.manager import MemoryManager, create_memory_manager
from nova.plugins.manager import PluginManager
from nova.voice.manager import VoiceManager, create_voice_manager

logger = get_logger(__name__)


@dataclass
class NovaContext:
    """A bundle holding every service Nova uses, built once at startup."""

    settings: Settings
    events: EventBus
    ai: LLMProvider
    memory: MemoryManager
    voice: VoiceManager
    commands: CommandRegistry
    plugins: PluginManager

    async def aclose(self) -> None:
        """Shut everything down cleanly (called when Nova stops)."""
        logger.info("Shutting down Nova...")
        await self.plugins.unload_all(self)


async def build_context(settings: Settings | None = None) -> NovaContext:
    """Create a fully wired `NovaContext`.

    Steps, in order (each piece may be used by the next):
      1. Load settings.
      2. Turn on logging.
      3. Build the event bus, memory, AI brain, and voice.
      4. Make an empty command registry.
      5. Discover and load plugins (which fill the command registry).
    """
    settings = settings or load_settings()
    setup_logging(level=settings.logging.level, json_format=settings.logging.json_format)
    logger.info("Starting Nova (AI provider: %s)", settings.ai.provider)

    events = EventBus()
    memory = create_memory_manager(settings.memory)
    ai = create_provider(settings.ai)
    voice = create_voice_manager(settings.voice)
    commands = CommandRegistry()
    plugins = PluginManager()

    context = NovaContext(
        settings=settings,
        events=events,
        ai=ai,
        memory=memory,
        voice=voice,
        commands=commands,
        plugins=plugins,
    )

    await plugins.load_all(context)
    logger.info(
        "Nova ready: %d plugin(s), %d command(s).",
        len(plugins.loaded),
        len(commands.all()),
    )
    return context

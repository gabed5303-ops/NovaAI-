"""The friendly "front desk" for memory that the rest of Nova talks to.

The manager hides which storage method is used behind nicer method names
(`remember`, `recall`, `forget`). It also knows how to build the right storage
method from your settings, and where to put the memory file by default.
"""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir

from nova.core.config import MemorySettings
from nova.core.exceptions import ConfigError
from nova.core.logging import get_logger
from nova.memory.base import MemoryStore
from nova.memory.models import MemoryRecord

logger = get_logger(__name__)


def default_memory_path() -> Path:
    """The standard per-user place to keep Nova's memory file on any OS.

    Examples:
      macOS:   ~/Library/Application Support/nova/memory.json
      Linux:   ~/.local/share/nova/memory.json
      Windows: C:\\Users\\You\\AppData\\Local\\nova\\memory.json
    """
    return Path(user_data_dir("nova", appauthor=False)) / "memory.json"


class MemoryManager:
    """A thin, friendly wrapper around a `MemoryStore`."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    async def remember(
        self,
        content: str,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryRecord:
        """Save something to memory."""
        return await self.store.add(content, tags=tags, metadata=metadata)

    async def recall(self, text: str, *, limit: int = 5) -> list[MemoryRecord]:
        """Find memories related to `text`."""
        return await self.store.query(text, limit=limit)

    async def forget(self, record_id: str) -> bool:
        """Delete a memory by ID."""
        return await self.store.forget(record_id)

    async def all(self) -> list[MemoryRecord]:
        """List every memory."""
        return await self.store.all()


def create_memory_manager(settings: MemorySettings) -> MemoryManager:
    """Build a `MemoryManager` using the storage method named in settings."""
    backend = settings.backend.lower().strip()

    if backend == "json":
        from nova.memory.backends.json_store import JsonMemoryStore

        path = Path(settings.path) if settings.path else default_memory_path()
        logger.info("Memory: JSON file at %s", path)
        return MemoryManager(JsonMemoryStore(path))

    raise ConfigError(
        f"Unknown memory backend '{settings.backend}'. Valid options: 'json'."
    )

"""The contract every memory-storage method must follow.

Any storage method (a JSON file today, a real database tomorrow) must inherit
from `MemoryStore` and implement these actions. Because they all share this
shape, Nova can switch storage methods by changing one setting.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from nova.memory.models import MemoryRecord


class MemoryStore(ABC):
    """Base template for a place that stores memories."""

    @abstractmethod
    async def add(
        self,
        content: str,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryRecord:
        """Save a new memory and return it (with its freshly-made ID)."""
        raise NotImplementedError

    @abstractmethod
    async def get(self, record_id: str) -> MemoryRecord | None:
        """Fetch one memory by ID, or None if it doesn't exist."""
        raise NotImplementedError

    @abstractmethod
    async def all(self) -> list[MemoryRecord]:
        """Return every saved memory."""
        raise NotImplementedError

    @abstractmethod
    async def query(self, text: str, *, limit: int = 10) -> list[MemoryRecord]:
        """Find memories related to `text`. Returns up to `limit` results.

        Today's JSON store does a simple text match; a future store could do
        smart "semantic" search here without changing this method's shape.
        """
        raise NotImplementedError

    @abstractmethod
    async def forget(self, record_id: str) -> bool:
        """Delete a memory by ID. Returns True if something was deleted."""
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """Delete ALL memories. Handy for tests and fresh starts."""
        raise NotImplementedError

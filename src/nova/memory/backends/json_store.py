"""The default memory storage: a plain JSON file on disk.

Why JSON? Because it needs zero setup — no database to install — and works the
same on macOS, Linux, and Windows. Perfect for getting started. The whole list
of memories is kept in the file and rewritten whenever it changes.

For big/serious use you'd swap this for a real database, but the `MemoryStore`
contract means nothing else in Nova would need to change.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from nova.core.logging import get_logger
from nova.memory.base import MemoryStore
from nova.memory.models import MemoryRecord

logger = get_logger(__name__)


class JsonMemoryStore(MemoryStore):
    """Stores memories as a list inside one JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._records: list[MemoryRecord] = []
        self._loaded = False
        # A lock stops two saves from happening at the exact same moment and
        # corrupting the file.
        self._lock = asyncio.Lock()

    # -- internal helpers -------------------------------------------------

    def _load_if_needed(self) -> None:
        """Read the file into memory the first time we need it."""
        if self._loaded:
            return
        if self.path.is_file():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._records = [MemoryRecord(**item) for item in raw]
            except (json.JSONDecodeError, TypeError, ValueError):
                logger.warning("Memory file %s was unreadable; starting empty.", self.path)
                self._records = []
        self._loaded = True

    def _save(self) -> None:
        """Write the current memories back to the file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [record.model_dump() for record in self._records]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # -- the contract -----------------------------------------------------

    async def add(
        self,
        content: str,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryRecord:
        async with self._lock:
            self._load_if_needed()
            record = MemoryRecord(
                id=uuid4().hex,
                content=content,
                tags=tags or [],
                metadata=metadata or {},
                created_at=datetime.now(UTC).isoformat(),
            )
            self._records.append(record)
            self._save()
            return record

    async def get(self, record_id: str) -> MemoryRecord | None:
        async with self._lock:
            self._load_if_needed()
            return next((r for r in self._records if r.id == record_id), None)

    async def all(self) -> list[MemoryRecord]:
        async with self._lock:
            self._load_if_needed()
            return list(self._records)

    async def query(self, text: str, *, limit: int = 10) -> list[MemoryRecord]:
        async with self._lock:
            self._load_if_needed()
            needle = text.lower().strip()
            if not needle:
                return list(self._records[:limit])
            # Simple match: the search text appears in the content or any tag.
            matches = [
                r
                for r in self._records
                if needle in r.content.lower()
                or any(needle in tag.lower() for tag in r.tags)
            ]
            return matches[:limit]

    async def forget(self, record_id: str) -> bool:
        async with self._lock:
            self._load_if_needed()
            before = len(self._records)
            self._records = [r for r in self._records if r.id != record_id]
            removed = len(self._records) < before
            if removed:
                self._save()
            return removed

    async def clear(self) -> None:
        async with self._lock:
            self._load_if_needed()
            self._records = []
            self._save()

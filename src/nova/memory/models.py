"""The shape of a single saved memory.

Each memory is one small note with an ID, the text itself, optional tags
(labels), optional extra info, and a timestamp of when it was saved.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    """One remembered item."""

    id: str = Field(description="Unique ID for this memory.")
    content: str = Field(description="The actual thing we're remembering.")
    tags: list[str] = Field(default_factory=list, description="Labels for grouping/search.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Optional extra key/value info."
    )
    created_at: str = Field(description="When it was saved (ISO 8601 timestamp).")

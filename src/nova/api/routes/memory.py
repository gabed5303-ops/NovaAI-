"""/memory endpoints — save, list, search, and delete memories."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nova.api.deps import get_context
from nova.api.schemas import MemoryIn
from nova.context import NovaContext
from nova.memory.models import MemoryRecord

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("", response_model=MemoryRecord)
async def remember(body: MemoryIn, context: NovaContext = Depends(get_context)) -> MemoryRecord:
    """Save a new memory."""
    return await context.memory.remember(
        body.content, tags=body.tags, metadata=body.metadata
    )


@router.get("", response_model=list[MemoryRecord])
async def list_memories(context: NovaContext = Depends(get_context)) -> list[MemoryRecord]:
    """List every saved memory."""
    return await context.memory.all()


@router.get("/search", response_model=list[MemoryRecord])
async def search_memories(
    q: str, limit: int = 5, context: NovaContext = Depends(get_context)
) -> list[MemoryRecord]:
    """Search memories whose text or tags contain `q`."""
    return await context.memory.recall(q, limit=limit)


@router.delete("/{record_id}")
async def forget_memory(
    record_id: str, context: NovaContext = Depends(get_context)
) -> dict[str, bool]:
    """Delete a memory by its ID."""
    deleted = await context.memory.forget(record_id)
    return {"deleted": deleted}

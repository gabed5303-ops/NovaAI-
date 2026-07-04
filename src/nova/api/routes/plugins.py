"""GET /plugins — list the add-on plugins that are currently loaded."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nova.api.deps import get_context
from nova.context import NovaContext

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("")
async def list_plugins(context: NovaContext = Depends(get_context)) -> list[dict[str, str]]:
    return [
        {"name": p.name, "version": p.version, "description": p.description}
        for p in context.plugins.loaded
    ]

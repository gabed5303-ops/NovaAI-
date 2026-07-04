"""GET /health — a quick "are you alive?" check.

Handy for you and for monitoring tools to confirm the server is running.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from nova import __version__
from nova.api.deps import get_context
from nova.context import NovaContext

router = APIRouter(tags=["system"])


@router.get("/health")
async def health(context: NovaContext = Depends(get_context)) -> dict[str, str]:
    return {
        "status": "ok",
        "service": "nova",
        "version": __version__,
        "ai_provider": context.settings.ai.provider,
    }

"""Shared helpers ("dependencies") that routes use to reach Nova's services.

FastAPI's `Depends(get_context)` lets any route ask for the `NovaContext` and
receive the one that was built at startup. This keeps routes short and testable.
"""

from __future__ import annotations

from fastapi import Request

from nova.context import NovaContext


def get_context(request: Request) -> NovaContext:
    """Return the app-wide NovaContext stored on the server at startup."""
    return request.app.state.context

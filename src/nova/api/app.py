"""Builds the FastAPI web application.

`create_app()` is a "factory": a function that makes a fresh app each time.
Factories are great for testing (each test gets a clean app).

The `lifespan` part runs code at startup (build the NovaContext) and at
shutdown (close it cleanly).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nova import __version__
from nova.api.routes import chat, commands, health, home, memory, plugins, voice, web
from nova.context import NovaContext, build_context
from nova.core.config import Settings


def create_app(
    settings: Settings | None = None,
    context: NovaContext | None = None,
) -> FastAPI:
    """Create the Nova web app.

    Args:
        settings: Optional settings to use. If None, loaded from config/env.
        context: Optional pre-built context (mainly for tests). If given, the
            app uses it and does NOT close it (the caller owns its lifecycle).
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # If a context was handed in, use it; otherwise build our own here.
        owns_context = context is None
        ctx = context or await build_context(settings)
        app.state.context = ctx
        try:
            yield  # <-- the server runs while we're paused here.
        finally:
            if owns_context:
                await ctx.aclose()

    app = FastAPI(
        title="Nova",
        description="A modular, JARVIS-inspired AI assistant.",
        version=__version__,
        lifespan=lifespan,
    )

    # Wire up every group of endpoints.
    app.include_router(home.router)  # the website homepage at "/"
    app.include_router(web.router)  # the chat app page at "/chat"
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(memory.router)
    app.include_router(voice.router)
    app.include_router(plugins.router)
    app.include_router(commands.router)

    return app

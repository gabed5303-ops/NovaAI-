"""A tiny "announcement system" (an event bus) for the app.

Imagine a bulletin board. Any part of Nova can:
  * "subscribe" to a topic (say "tell me whenever a command finishes"), or
  * "publish" to a topic (say "hey, a command just finished!").

This lets different parts of Nova react to each other WITHOUT being wired
directly together — which keeps the code loosely coupled and easy to change.
Later, JARVIS-style behaviors ("on wake word", "on command complete") build on this.
"""

from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from nova.core.logging import get_logger

logger = get_logger(__name__)

# A handler is a function that takes the event's payload. It may be a normal
# function OR an async one (we handle both).
EventHandler = Callable[[Any], None | Awaitable[None]]


class EventBus:
    """Keeps track of who wants to hear about which events, and notifies them."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event: str, handler: EventHandler) -> None:
        """Ask to be notified whenever `event` is published."""
        self._subscribers[event].append(handler)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        """Stop being notified about `event`. Does nothing if not subscribed."""
        if handler in self._subscribers.get(event, []):
            self._subscribers[event].remove(handler)

    async def publish(self, event: str, payload: Any = None) -> None:
        """Announce that `event` happened, and run every subscriber's handler.

        Handlers can be normal or async functions. If one handler crashes, we
        log it and keep going so a single bad handler can't take down the rest.
        """
        for handler in list(self._subscribers.get(event, [])):
            try:
                result = handler(payload)
                if inspect.isawaitable(result):
                    await result
            except Exception:  # noqa: BLE001 - we intentionally isolate handlers.
                logger.exception("Event handler for %r failed", event)

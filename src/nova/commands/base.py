"""What a "command" is.

A command is one named action, like "hello" or "weather". Every command has:
  * a `name`  (how you call it)
  * a `description` (what it does)
  * a `run(args)` method (the actual work), where `args` is a dict of inputs.

Two ways to make one:
  1. Subclass `Command` and write a `run` method (good for bigger actions).
  2. Wrap a plain async function with `FunctionCommand` (quick and easy).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any


class Command(ABC):
    """Base template for an action Nova can run."""

    name: str = "unnamed"
    description: str = ""

    @abstractmethod
    async def run(self, args: dict[str, Any]) -> Any:
        """Do the action. `args` holds any inputs; return any result."""
        raise NotImplementedError


class FunctionCommand(Command):
    """Turn a plain async function into a Command — the quick way.

    Example:
        async def _ping(args): return "pong"
        registry.register(FunctionCommand("ping", "Replies with pong.", _ping))
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[[dict[str, Any]], Awaitable[Any]],
    ) -> None:
        self.name = name
        self.description = description
        self._func = func

    async def run(self, args: dict[str, Any]) -> Any:
        return await self._func(args)

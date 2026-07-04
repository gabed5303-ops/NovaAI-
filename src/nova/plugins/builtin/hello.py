"""A tiny example plugin that adds a `hello` command.

Its whole job is to prove the plugin system works end-to-end:
  plugin is discovered -> loaded -> registers a command -> command can be run.

Use it as a template for your own plugins: copy this file, rename things, and
put your own logic in the command's `run` method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nova.commands.base import Command
from nova.plugins.base import Plugin

if TYPE_CHECKING:
    from nova.context import NovaContext


class HelloCommand(Command):
    """Says hello. Optionally greets a specific name."""

    name = "hello"
    description = "Greets you. Pass {\"name\": \"Ada\"} to greet a specific name."

    async def run(self, args: dict[str, Any]) -> dict[str, str]:
        who = str(args.get("name", "world"))
        return {"message": f"Hello, {who}! Nova is up and running."}


class HelloPlugin(Plugin):
    """Registers the `hello` command when Nova starts."""

    name = "hello"
    version = "0.1.0"
    description = "A friendly example plugin that adds the 'hello' command."

    async def setup(self, context: NovaContext) -> None:
        context.commands.register(HelloCommand())

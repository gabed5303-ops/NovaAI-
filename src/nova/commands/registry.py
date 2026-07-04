"""The command "phone book": remembers every command by name and runs them.

Plugins call `register(...)` to add their commands here. The API layer calls
`run(name, args)` to execute one.
"""

from __future__ import annotations

from typing import Any

from nova.commands.base import Command
from nova.core.exceptions import CommandError
from nova.core.logging import get_logger

logger = get_logger(__name__)


class CommandRegistry:
    """Holds all known commands and runs them on request."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """Add a command. Errors if the name is already taken."""
        if command.name in self._commands:
            raise CommandError(f"A command named '{command.name}' is already registered.")
        self._commands[command.name] = command
        logger.debug("Registered command: %s", command.name)

    def unregister(self, name: str) -> None:
        """Remove a command by name (ignored if it doesn't exist)."""
        self._commands.pop(name, None)

    def get(self, name: str) -> Command | None:
        """Look up a command by name, or None if not found."""
        return self._commands.get(name)

    def all(self) -> list[Command]:
        """List every registered command."""
        return list(self._commands.values())

    async def run(self, name: str, args: dict[str, Any] | None = None) -> Any:
        """Run the named command with the given inputs."""
        command = self.get(name)
        if command is None:
            raise CommandError(f"No command named '{name}'.")
        return await command.run(args or {})

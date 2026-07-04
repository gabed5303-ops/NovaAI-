"""What a "plugin" is.

A plugin is an add-on pack that teaches Nova new tricks. When Nova starts, it
calls each plugin's `setup(context)`. Inside `setup`, a plugin can:
  * register new commands   -> context.commands.register(...)
  * listen for events        -> context.events.subscribe(...)
  * use memory or the AI     -> context.memory, context.ai

When Nova shuts down, it calls `teardown(context)` so plugins can clean up.

`setup` and `teardown` have do-nothing defaults, so a simple plugin only writes
the parts it actually needs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Imported only for type hints to avoid a circular import at runtime
    # (context.py imports the plugin manager, which imports this file).
    from nova.context import NovaContext


class Plugin:
    """Base template for a Nova add-on.

    This is a plain base class (not abstract) on purpose: `setup` and `teardown`
    are OPTIONAL. A plugin overrides only the hooks it actually needs.
    """

    #: A short unique name for the plugin, e.g. "hello".
    name: str = "unnamed"
    #: The plugin's version.
    version: str = "0.1.0"
    #: A one-line description of what it adds.
    description: str = ""

    async def setup(self, context: NovaContext) -> None:
        """Run once when Nova starts. Register commands/events here."""

    async def teardown(self, context: NovaContext) -> None:
        """Run once when Nova stops. Undo anything from setup here."""

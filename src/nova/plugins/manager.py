"""Finds and runs plugins.

Two ways a plugin is discovered:
  1. BUILT-IN: any `Plugin` subclass inside the `nova.plugins.builtin` package.
  2. THIRD-PARTY: any package that advertises itself under the "nova.plugins"
     entry-point group. This is how someone could `pip install nova-weather`
     and have it picked up automatically — no core changes needed.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import pkgutil
from types import ModuleType
from typing import TYPE_CHECKING

from nova.core.logging import get_logger
from nova.plugins.base import Plugin

if TYPE_CHECKING:
    from nova.context import NovaContext

logger = get_logger(__name__)

ENTRY_POINT_GROUP = "nova.plugins"


class PluginManager:
    """Discovers plugins, and runs their setup/teardown lifecycle."""

    def __init__(self) -> None:
        self._loaded: list[Plugin] = []

    # -- discovery --------------------------------------------------------

    def discover(self) -> list[type[Plugin]]:
        """Find every available plugin CLASS (built-in + third-party)."""
        return self._discover_builtin() + self._discover_entry_points()

    def _discover_builtin(self) -> list[type[Plugin]]:
        import nova.plugins.builtin as builtin_pkg

        found: list[type[Plugin]] = []
        for module_info in pkgutil.iter_modules(
            builtin_pkg.__path__, builtin_pkg.__name__ + "."
        ):
            try:
                module = importlib.import_module(module_info.name)
            except Exception:  # noqa: BLE001 - one bad module shouldn't block others.
                logger.exception("Could not import built-in plugin module %s", module_info.name)
                continue
            found.extend(self._plugin_classes_in(module))
        return found

    def _discover_entry_points(self) -> list[type[Plugin]]:
        found: list[type[Plugin]] = []
        try:
            entry_points = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
        except Exception:  # noqa: BLE001 - be tolerant of odd environments.
            logger.exception("Could not read plugin entry points.")
            return found

        for entry_point in entry_points:
            try:
                obj = entry_point.load()
            except Exception:  # noqa: BLE001
                logger.exception("Could not load plugin entry point %s", entry_point.name)
                continue
            if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                found.append(obj)
            else:
                logger.warning(
                    "Entry point %s did not point to a Plugin subclass; skipping.",
                    entry_point.name,
                )
        return found

    @staticmethod
    def _plugin_classes_in(module: ModuleType) -> list[type[Plugin]]:
        """Return the Plugin subclasses DEFINED in this module (not imported ones)."""
        classes: list[type[Plugin]] = []
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, Plugin)
                and value is not Plugin
                and value.__module__ == module.__name__
            ):
                classes.append(value)
        return classes

    # -- lifecycle --------------------------------------------------------

    async def load_all(self, context: NovaContext) -> None:
        """Create each discovered plugin and run its `setup`."""
        for plugin_cls in self.discover():
            try:
                plugin = plugin_cls()
                await plugin.setup(context)
                self._loaded.append(plugin)
                logger.info("Loaded plugin: %s v%s", plugin.name, plugin.version)
            except Exception:  # noqa: BLE001 - a broken plugin must not crash Nova.
                logger.exception("Failed to load plugin %s", plugin_cls)

    async def unload_all(self, context: NovaContext) -> None:
        """Run each loaded plugin's `teardown`, in reverse order."""
        for plugin in reversed(self._loaded):
            try:
                await plugin.teardown(context)
            except Exception:  # noqa: BLE001
                logger.exception("Error while unloading plugin %s", plugin.name)
        self._loaded.clear()

    @property
    def loaded(self) -> list[Plugin]:
        """The plugins currently loaded and running."""
        return list(self._loaded)

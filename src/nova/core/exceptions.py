"""All of Nova's custom error types live here.

Why have our own errors? So that when something goes wrong we can say *what kind*
of thing went wrong (a config problem? an AI problem?) instead of a vague crash.
Every Nova error is a `NovaError`, so code can catch "any Nova problem" easily.
"""

from __future__ import annotations


class NovaError(Exception):
    """Base class for every error Nova raises on purpose."""


class ConfigError(NovaError):
    """Something is wrong with the settings/config (e.g. a bad value)."""


class ProviderUnavailableError(NovaError):
    """An AI provider can't be used right now (missing key, server offline, etc.)."""


class PluginError(NovaError):
    """A plugin failed to load or misbehaved."""


class CommandError(NovaError):
    """A command could not be found or failed while running."""

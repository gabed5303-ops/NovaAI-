"""Sets up "logging" — Nova's way of printing helpful messages about what it's doing.

Instead of scattering `print()` calls everywhere, we use Python's logging system.
Benefits: we can turn the detail level up or down, and (optionally) print messages
as JSON so other programs can read them.
"""

from __future__ import annotations

import json
import logging
import sys


class _JsonFormatter(logging.Formatter):
    """Turns a log message into a single line of JSON.

    Useful in production where log-collecting tools prefer JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """Configure how Nova prints log messages.

    Args:
        level: How chatty to be — "DEBUG" (everything), "INFO" (normal),
            "WARNING", or "ERROR" (only problems).
        json_format: If True, print logs as JSON lines instead of plain text.
    """
    handler = logging.StreamHandler(stream=sys.stderr)
    if json_format:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-7s  %(name)s  %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()  # Remove any handlers added earlier so we don't double-print.
    root.addHandler(handler)
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Convention: call `get_logger(__name__)` in each file."""
    return logging.getLogger(name)

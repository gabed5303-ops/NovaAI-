"""The starting point that runs Nova's web server.

Two ways to start Nova, both land here:
    nova                      (the command installed from pyproject.toml)
    python -m nova            (running the package directly)

It reads your settings to know which address/port to use, then hands the app
to `uvicorn`, the program that actually serves web requests.
"""

from __future__ import annotations

import uvicorn

from nova.api.app import create_app
from nova.core.config import load_settings


def run() -> None:
    """Load settings and start the web server."""
    settings = load_settings()
    # We pass an import string ("nova.api.app:...") only when reload is on, because
    # auto-reload needs to be able to re-import the app. Otherwise we build it here.
    uvicorn.run(
        create_app(settings),
        host=settings.server.host,
        port=settings.server.port,
        reload=False,
    )


if __name__ == "__main__":
    run()

"""Shared test setup ("fixtures") that every test file can use.

A fixture is a reusable helper pytest hands to a test when the test asks for it
by name. Here we provide:
  * `settings` — Nova settings pointed at a TEMPORARY memory file, so tests never
    touch your real saved memories.
  * `client`   — a fake web client that talks to the app in-process (no real
    network, no real server), so tests are fast and isolated.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nova.api.app import create_app
from nova.core.config import MemorySettings, Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings that store memory in a throwaway temp folder for this test."""
    memory_file = tmp_path / "memory.json"
    return Settings(memory=MemorySettings(path=str(memory_file)))


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """A test client. Entering the `with` block runs Nova's startup logic."""
    app = create_app(settings=settings)
    with TestClient(app) as test_client:
        yield test_client

"""Test that the plugin system discovers and loads the built-in `hello` plugin."""

from __future__ import annotations

from fastapi.testclient import TestClient

from nova.plugins.manager import PluginManager


def test_discovery_finds_builtin_hello() -> None:
    classes = PluginManager().discover()
    names = [cls.name for cls in classes]
    assert "hello" in names


def test_hello_plugin_is_loaded(client: TestClient) -> None:
    response = client.get("/plugins")
    assert response.status_code == 200

    names = [plugin["name"] for plugin in response.json()]
    assert "hello" in names

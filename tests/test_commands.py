"""Test listing and running commands — proves the plugin -> command chain works."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_hello_command_is_listed(client: TestClient) -> None:
    response = client.get("/commands")
    assert any(cmd["name"] == "hello" for cmd in response.json())


def test_run_hello_command(client: TestClient) -> None:
    response = client.post("/commands/hello", json={"args": {"name": "Ada"}})
    assert response.status_code == 200
    assert "Ada" in response.json()["result"]["message"]


def test_run_hello_without_args(client: TestClient) -> None:
    # Sending no body should still work (defaults to greeting "world").
    response = client.post("/commands/hello")
    assert response.status_code == 200
    assert "world" in response.json()["result"]["message"]


def test_unknown_command_returns_404(client: TestClient) -> None:
    response = client.post("/commands/does-not-exist")
    assert response.status_code == 404

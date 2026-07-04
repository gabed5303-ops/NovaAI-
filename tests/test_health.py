"""Test the /health endpoint — the simplest proof the server works."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "nova"
    assert data["ai_provider"] == "ollama"  # the default provider

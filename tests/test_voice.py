"""Test the placeholder voice endpoints (text->audio and audio->text)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_text_to_speech_returns_bytes(client: TestClient) -> None:
    response = client.post("/voice/tts", json={"text": "hello there"})
    assert response.status_code == 200
    assert response.headers["X-Voice-Engine"] == "placeholder"
    assert len(response.content) > 0


def test_speech_to_text_returns_text(client: TestClient) -> None:
    response = client.post("/voice/stt", content=b"pretend-this-is-audio")
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "placeholder"
    assert "placeholder" in body["text"]

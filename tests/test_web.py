"""Test the website pages: the homepage (/) and the chat app page (/chat)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_homepage_loads(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Storefront essentials are present.
    assert "Nova" in response.text
    assert "Pricing" in response.text
    assert "/chat" in response.text  # the "Open Chat" call-to-action


def test_chat_page_loads(client: TestClient) -> None:
    response = client.get("/chat")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Message Nova" in response.text  # the composer placeholder


def test_chat_api_still_posts(client: TestClient) -> None:
    # GET /chat is the page; POST /chat is still the API. With no AI model
    # running in tests, the API should fail cleanly (503), not break routing.
    response = client.post("/chat", json={"message": "hi"})
    assert response.status_code in (200, 503)

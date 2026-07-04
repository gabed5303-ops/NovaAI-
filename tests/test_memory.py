"""Test the memory system — both the storage directly and through the web API."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nova.memory.backends.json_store import JsonMemoryStore


async def test_json_store_roundtrip(tmp_path: Path) -> None:
    store = JsonMemoryStore(tmp_path / "memory.json")

    record = await store.add("I like green tea", tags=["preference"])
    assert record.id
    assert record.created_at

    # It can be found by content...
    by_content = await store.query("green tea")
    assert len(by_content) == 1
    # ...and by tag.
    by_tag = await store.query("preference")
    assert len(by_tag) == 1

    # It can be fetched by ID.
    fetched = await store.get(record.id)
    assert fetched is not None and fetched.content == "I like green tea"

    # And forgotten.
    assert await store.forget(record.id) is True
    assert await store.all() == []


async def test_json_store_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "memory.json"
    store1 = JsonMemoryStore(path)
    await store1.add("remember me")

    # A brand-new store reading the same file should see the saved memory.
    store2 = JsonMemoryStore(path)
    all_records = await store2.all()
    assert len(all_records) == 1
    assert all_records[0].content == "remember me"


def test_memory_api(client: TestClient) -> None:
    created = client.post("/memory", json={"content": "buy milk", "tags": ["todo"]})
    assert created.status_code == 200
    record = created.json()

    found = client.get("/memory/search", params={"q": "milk"})
    assert any(m["content"] == "buy milk" for m in found.json())

    deleted = client.delete(f"/memory/{record['id']}")
    assert deleted.json()["deleted"] is True

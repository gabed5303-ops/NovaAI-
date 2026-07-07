"""Test the reminders plugin: parsing, the save/list/complete flow, and due firing."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nova.core.events import EventBus
from nova.plugins.builtin.reminders import (
    REMINDER_DUE_EVENT,
    CompleteReminderCommand,
    ListRemindersCommand,
    ReminderStore,
    RemindMeCommand,
    _applescript_quote,
    check_due_reminders,
    parse_when,
)
from nova.plugins.manager import PluginManager

NOW = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)


def test_discovery_finds_reminders() -> None:
    names = [cls.name for cls in PluginManager().discover()]
    assert "reminders" in names


# -- time parsing ----------------------------------------------------------


def test_parse_relative_times() -> None:
    assert parse_when("in 10 minutes", NOW) == NOW + timedelta(minutes=10)
    assert parse_when("in 2 hours", NOW) == NOW + timedelta(hours=2)
    assert parse_when("IN 1 DAY", NOW) == NOW + timedelta(days=1)


def test_parse_clock_times() -> None:
    assert parse_when("3pm", NOW) == NOW.replace(hour=15, minute=0)
    assert parse_when("at 11:45", NOW) == NOW.replace(hour=11, minute=45)
    # 9am has already passed at NOW (10:00), so it means tomorrow 9am.
    assert parse_when("9am", NOW) == NOW.replace(hour=9) + timedelta(days=1)
    # The 12 o'clock quirks.
    assert parse_when("12pm", NOW) == NOW.replace(hour=12, minute=0)
    assert parse_when("12am", NOW) == NOW.replace(hour=0, minute=0) + timedelta(days=1)


def test_parse_tomorrow_and_iso() -> None:
    assert parse_when("tomorrow", NOW) == NOW.replace(hour=9) + timedelta(days=1)
    assert parse_when("tomorrow at 6pm", NOW) == NOW.replace(hour=18) + timedelta(days=1)
    parsed = parse_when("2026-12-25 08:30", NOW)
    assert parsed is not None
    assert (parsed.month, parsed.day, parsed.hour, parsed.minute) == (12, 25, 8, 30)


def test_parse_nonsense_returns_none() -> None:
    for junk in ["whenever", "at 25:99", "in minutes", ""]:
        assert parse_when(junk, NOW) is None, f"{junk!r} should not parse"


# -- the command flow ------------------------------------------------------


async def test_remind_list_complete_flow(tmp_path: Path) -> None:
    store = ReminderStore(tmp_path / "reminders.json")

    saved = await RemindMeCommand(store).run({"text": "feed the cat", "when": "in 2 hours"})
    assert saved["saved"] is True

    listed = await ListRemindersCommand(store).run({})
    assert listed["count"] == 1
    assert listed["reminders"][0]["text"] == "feed the cat"
    assert listed["reminders"][0]["overdue"] is False

    done = await CompleteReminderCommand(store).run({"reminder": "feed the"})
    assert done["completed"] is True

    assert (await ListRemindersCommand(store).run({}))["count"] == 0
    assert (await ListRemindersCommand(store).run({"include_done": True}))["count"] == 1


async def test_remind_me_rejects_bad_time(tmp_path: Path) -> None:
    store = ReminderStore(tmp_path / "reminders.json")
    result = await RemindMeCommand(store).run({"text": "x", "when": "sometime soonish"})
    assert "error" in result
    assert "accepted_formats" in result


async def test_complete_is_ambiguous_with_two_matches(tmp_path: Path) -> None:
    store = ReminderStore(tmp_path / "reminders.json")
    await store.add("call mom", None)
    await store.add("call dentist", None)

    result = await CompleteReminderCommand(store).run({"reminder": "call"})
    assert "error" in result
    assert len(result["candidates"]) == 2


async def test_reminders_survive_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "reminders.json"
    await ReminderStore(path).add("water the plants", None)

    listed = await ListRemindersCommand(ReminderStore(path)).run({})
    assert listed["count"] == 1


# -- due checking + the event bus ------------------------------------------


async def test_due_reminder_fires_event_exactly_once(tmp_path: Path) -> None:
    store = ReminderStore(tmp_path / "reminders.json")
    events = EventBus()
    heard: list[dict] = []
    events.subscribe(REMINDER_DUE_EVENT, heard.append)

    past = datetime.now().astimezone() - timedelta(minutes=1)
    future = datetime.now().astimezone() + timedelta(hours=1)
    await store.add("already due", past)
    await store.add("not yet", future)

    fired = await check_due_reminders(store, events)
    assert [r.text for r in fired] == ["already due"]
    assert heard[0]["text"] == "already due"

    # A second sweep must not announce it again.
    assert await check_due_reminders(store, events) == []
    assert len(heard) == 1


async def test_done_reminders_never_fire(tmp_path: Path) -> None:
    store = ReminderStore(tmp_path / "reminders.json")
    past = datetime.now().astimezone() - timedelta(minutes=5)
    saved = await store.add("stale task", past)
    await store.set_done(saved.id)

    assert await check_due_reminders(store, EventBus()) == []


async def test_naive_due_at_does_not_break_the_sweep(tmp_path: Path) -> None:
    """A hand-edited file with a timezone-less due_at must not crash firing."""
    path = tmp_path / "reminders.json"
    # A naive datetime string (no offset) — exactly what a hand-edit produces,
    # and a format the plugin itself advertises ("2026-07-15 14:00").
    path.write_text(
        json.dumps(
            [
                {
                    "id": "a" * 32,
                    "text": "naive one",
                    "created_at": "2000-01-01T00:00:00",
                    "due_at": "2000-01-01 09:00",
                    "done": False,
                    "notified": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    store = ReminderStore(path)
    # A genuinely-due, well-formed reminder alongside the bad one.
    await store.add("good one", datetime.now().astimezone() - timedelta(minutes=1))

    fired = await check_due_reminders(store, EventBus())
    fired_texts = {r.text for r in fired}
    # The good one still fires; the naive one is handled (past date => also due),
    # and crucially nothing raised.
    assert "good one" in fired_texts


async def test_null_args_are_handled(tmp_path: Path) -> None:
    store = ReminderStore(tmp_path / "reminders.json")

    # Explicit null 'when' => a valid reminder with no time (not an error).
    saved = await RemindMeCommand(store).run({"text": "buy milk", "when": None})
    assert saved.get("saved") is True
    assert saved["due_at"] is None

    # Explicit null 'text' => rejected as empty, never saved as "None".
    rejected = await RemindMeCommand(store).run({"text": None, "when": "in 5 minutes"})
    assert "error" in rejected

    listed = await ListRemindersCommand(store).run({})
    assert [r["text"] for r in listed["reminders"]] == ["buy milk"]
    assert "None" not in [r["text"] for r in listed["reminders"]]


# -- notification safety ----------------------------------------------------


def test_applescript_quoting_neutralizes_injection() -> None:
    hostile = 'pwned" with title "gotcha\\" & do shell script "id'
    quoted = _applescript_quote(hostile)
    # Every quote and backslash must arrive escaped — nothing can close the
    # string literal early.
    assert '\\"' in quoted
    assert not re.search(r'(?<!\\)"', quoted)

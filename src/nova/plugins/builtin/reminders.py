"""Reminders: "remind me to take out the trash at 6pm" — and Nova follows up.

How it works, end to end:
  1. `remind_me` saves the reminder to its own JSON file (reminders.json, kept
     right next to Nova's memory.json — same simple storage style).
  2. A small background loop wakes every few seconds and asks "is anything due?"
  3. When a reminder comes due, the loop publishes a "reminder.due" event on
     Nova's event bus. Anything can subscribe to that event; this plugin ships
     one subscriber that logs it and (on macOS) pops a desktop notification.

Times are handled in YOUR local timezone, since "remind me at 6pm" means 6pm
on the clock on the wall, not 6pm somewhere else.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, tzinfo
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel

from nova.commands.base import Command
from nova.core.events import EventBus
from nova.core.logging import get_logger
from nova.plugins.base import Plugin

if TYPE_CHECKING:
    from nova.context import NovaContext

logger = get_logger(__name__)

# The event published when a reminder comes due. Payload: {id, text, due_at}.
REMINDER_DUE_EVENT = "reminder.due"

# What `remind_me`'s "when" accepts — shown back to the AI if parsing fails.
ACCEPTED_TIME_FORMATS = [
    "in 10 minutes / in 2 hours / in 3 days",
    "3pm / 15:30 / at 9:45am (today, or tomorrow if already past)",
    "tomorrow / tomorrow at 8am",
    "2026-07-15 14:00 (a full date and time)",
]


def _resolve_local_zone() -> tzinfo:
    """Find the user's real timezone so reminders stay correct across DST.

    A named zone (like 'America/New_York') knows that clocks shift in spring
    and fall; a plain UTC offset doesn't. We look for the zone the OS is set to
    ($TZ, or the /etc/localtime symlink on macOS/Linux) and fall back to the
    current fixed offset if we can't find a named one (e.g. on Windows).
    """
    tz_name = os.environ.get("TZ")
    if tz_name:
        with contextlib.suppress(ZoneInfoNotFoundError, ValueError):
            return ZoneInfo(tz_name)

    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        target = os.readlink(localtime)
        marker = "zoneinfo/"
        if marker in target:
            with contextlib.suppress(ZoneInfoNotFoundError, ValueError):
                return ZoneInfo(target.split(marker, 1)[1])

    # Last resort: a fixed offset (correct now, but blind to future DST shifts).
    return datetime.now().astimezone().tzinfo or ZoneInfo("UTC")


# The zone is read once — it doesn't change while Nova is running.
_LOCAL_ZONE: tzinfo = _resolve_local_zone()


def _local_now() -> datetime:
    """The current time in the user's local timezone (timezone-aware)."""
    return datetime.now(_LOCAL_ZONE)


def _parse_due(value: str | None) -> datetime | None:
    """Read a stored due_at string into an aware datetime, or None if unusable.

    Tolerant on purpose: a hand-edited or older file might hold a datetime with
    no timezone. We treat such a value as local time rather than letting it
    crash a comparison (naive vs. aware datetimes raise TypeError).
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_LOCAL_ZONE)
    return parsed


class Reminder(BaseModel):
    """One saved reminder."""

    id: str
    text: str
    created_at: str  # ISO timestamp
    due_at: str | None = None  # ISO timestamp, or None for "no particular time"
    done: bool = False
    notified: bool = False  # True once the "it's due!" event has fired


# ---------------------------------------------------------------------------
# Time parsing — small on purpose. No libraries, no network, just the phrases
# people actually use with an assistant.
# ---------------------------------------------------------------------------

_RELATIVE_RE = re.compile(
    r"^in\s+(\d{1,4})\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?)$", re.IGNORECASE
)
_CLOCK_RE = re.compile(r"^(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", re.IGNORECASE)

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_clock(text: str, base: datetime) -> datetime | None:
    """Parse '3pm', '15:30', 'at 9:45am' as a time on `base`'s date."""
    match = _CLOCK_RE.match(text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = (match.group(3) or "").lower()

    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def parse_when(text: str, now: datetime | None = None) -> datetime | None:
    """Turn a human phrase into a timezone-aware datetime, or None if we can't."""
    now = now or _local_now()
    cleaned = " ".join(text.strip().lower().split())
    if not cleaned:
        return None

    # "in 10 minutes"
    match = _RELATIVE_RE.match(cleaned)
    if match:
        amount = int(match.group(1))
        unit_seconds = _UNIT_SECONDS[match.group(2)[0]]
        return now + timedelta(seconds=amount * unit_seconds)

    # "tomorrow" / "tomorrow at 8am"
    if cleaned == "tomorrow":
        return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    if cleaned.startswith("tomorrow "):
        clock = _parse_clock(cleaned.removeprefix("tomorrow ").strip(), now + timedelta(days=1))
        if clock is not None:
            return clock

    # "3pm" / "15:30" / "at 9:45am" — today, or tomorrow if that time has passed.
    clock = _parse_clock(cleaned, now)
    if clock is not None:
        if clock <= now:
            clock += timedelta(days=1)
        return clock

    # A full date/time like "2026-07-15 14:00" or "2026-07-15T14:00".
    try:
        parsed = datetime.fromisoformat(text.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=now.tzinfo)
    return parsed


# ---------------------------------------------------------------------------
# Storage — same recipe as Nova's JSON memory store: one small file, an
# asyncio lock so two writes can't collide, tolerant of a corrupted file.
# ---------------------------------------------------------------------------


class ReminderStore:
    """Keeps reminders as a list inside one JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._reminders: list[Reminder] = []
        self._loaded = False
        self._lock = asyncio.Lock()

    def _load_if_needed(self) -> None:
        if self._loaded:
            return
        if self.path.is_file():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._reminders = [Reminder(**item) for item in raw]
            except (json.JSONDecodeError, TypeError, ValueError):
                logger.warning("Reminders file %s was unreadable; starting empty.", self.path)
                self._reminders = []
        self._loaded = True

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [reminder.model_dump() for reminder in self._reminders]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    async def add(self, text: str, due_at: datetime | None) -> Reminder:
        async with self._lock:
            self._load_if_needed()
            reminder = Reminder(
                id=uuid4().hex,
                text=text,
                created_at=_local_now().isoformat(),
                due_at=due_at.isoformat() if due_at else None,
            )
            self._reminders.append(reminder)
            self._save()
            return reminder

    async def all(self) -> list[Reminder]:
        async with self._lock:
            self._load_if_needed()
            return list(self._reminders)

    async def set_done(self, reminder_id: str) -> Reminder | None:
        async with self._lock:
            self._load_if_needed()
            for reminder in self._reminders:
                if reminder.id == reminder_id:
                    reminder.done = True
                    self._save()
                    return reminder
            return None

    async def pop_due(self, now: datetime) -> list[Reminder]:
        """Return reminders that are due and unannounced, marking them announced.

        Marking happens in the same locked step as finding, so a reminder can
        never be announced twice even if two checks overlap.
        """
        async with self._lock:
            self._load_if_needed()
            due: list[Reminder] = []
            for reminder in self._reminders:
                if reminder.done or reminder.notified or reminder.due_at is None:
                    continue
                due_at = _parse_due(reminder.due_at)
                if due_at is None:
                    continue  # A hand-edited bad date shouldn't break the loop.
                if due_at <= now:
                    reminder.notified = True
                    due.append(reminder)
            if due:
                self._save()
            return due


# ---------------------------------------------------------------------------
# The commands the AI (and the API) can call.
# ---------------------------------------------------------------------------


class RemindMeCommand(Command):
    """Save a new reminder."""

    name = "remind_me"
    description = (
        "Save a reminder for the user, optionally with a time. Use when the user "
        "says 'remind me to ...'. Pass the time phrase in 'when' (e.g. 'in 20 "
        "minutes', '6pm', 'tomorrow at 8am') — omit it for a reminder with no time."
    )
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "What to remind the user about, e.g. 'take out the trash'.",
            },
            "when": {
                "type": "string",
                "description": (
                    "When it's due: 'in 10 minutes', '3pm', 'tomorrow at 8am', "
                    "or '2026-07-15 14:00'. Optional."
                ),
            },
        },
        "required": ["text"],
    }

    def __init__(self, store: ReminderStore) -> None:
        self._store = store

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        # `or ""` (not a get-default) so an explicit null from the LLM becomes
        # empty, not the literal string "None" — a null 'when' means "no time",
        # and a null 'text' is correctly rejected as empty.
        text = str(args.get("text") or "").strip()
        if not text:
            return {"error": "Nothing to remind about — 'text' was empty."}

        when_phrase = str(args.get("when") or "").strip()
        due_at: datetime | None = None
        if when_phrase:
            due_at = parse_when(when_phrase)
            if due_at is None:
                return {
                    "error": f"Couldn't understand the time {when_phrase!r}.",
                    "accepted_formats": ACCEPTED_TIME_FORMATS,
                }

        reminder = await self._store.add(text, due_at)
        result: dict[str, Any] = {"saved": True, "id": reminder.id, "text": reminder.text}
        if due_at is not None:
            result["due_at"] = due_at.strftime("%Y-%m-%d %H:%M %Z")
        else:
            result["due_at"] = None
        return result


class ListRemindersCommand(Command):
    """Show saved reminders."""

    name = "list_reminders"
    description = (
        "List the user's reminders (active ones by default). Use when asked "
        "'what are my reminders?' or before marking one done."
    )
    parameters = {
        "type": "object",
        "properties": {
            "include_done": {
                "type": "boolean",
                "description": "Also include completed reminders (default: false).",
            },
        },
    }

    def __init__(self, store: ReminderStore) -> None:
        self._store = store

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        include_done = bool(args.get("include_done", False))
        now = _local_now()

        reminders = await self._store.all()
        if not include_done:
            reminders = [r for r in reminders if not r.done]

        # Timed reminders first (soonest first), then the "whenever" ones.
        # Sort timed ones by their real instant, not the raw string — two
        # reminders written in different UTC offsets don't sort right as text.
        # (The 0/1 group tag keeps datetimes and strings from ever comparing.)
        def sort_key(r: Reminder) -> tuple[int, datetime | str]:
            due = _parse_due(r.due_at)
            return (0, due) if due is not None else (1, r.created_at)

        items: list[dict[str, Any]] = []
        for reminder in sorted(reminders, key=sort_key):
            item: dict[str, Any] = {
                "id": reminder.id,
                "text": reminder.text,
                "due_at": reminder.due_at,
                "done": reminder.done,
            }
            due = _parse_due(reminder.due_at)
            if due is not None and not reminder.done:
                item["overdue"] = due <= now
            items.append(item)
        return {"count": len(items), "reminders": items}


class CompleteReminderCommand(Command):
    """Mark a reminder as done."""

    name = "complete_reminder"
    description = (
        "Mark a reminder as done. Pass the reminder's id (from list_reminders) "
        "or a few words from its text."
    )
    parameters = {
        "type": "object",
        "properties": {
            "reminder": {
                "type": "string",
                "description": "The reminder's id, or a unique fragment of its text.",
            },
        },
        "required": ["reminder"],
    }

    def __init__(self, store: ReminderStore) -> None:
        self._store = store

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        needle = str(args.get("reminder") or "").strip()
        if not needle:
            return {"error": "Say which reminder — an id or a few words from its text."}

        active = [r for r in await self._store.all() if not r.done]

        # Try the id first (full or a prefix), then words from the text.
        matches = [r for r in active if r.id == needle or r.id.startswith(needle)]
        if not matches:
            matches = [r for r in active if needle.lower() in r.text.lower()]

        if not matches:
            return {"error": f"No active reminder matches {needle!r}."}
        if len(matches) > 1:
            return {
                "error": f"{needle!r} matches several reminders — be more specific.",
                "candidates": [{"id": r.id, "text": r.text} for r in matches],
            }

        done = await self._store.set_done(matches[0].id)
        assert done is not None  # It was just found; the store still has it.
        return {"completed": True, "id": done.id, "text": done.text}


# ---------------------------------------------------------------------------
# The "actually notify me" part: a background check loop + event subscriber.
# ---------------------------------------------------------------------------


async def check_due_reminders(store: ReminderStore, events: EventBus) -> list[Reminder]:
    """One sweep: announce every newly-due reminder on the event bus."""
    due = await store.pop_due(_local_now())
    for reminder in due:
        logger.info("Reminder due: %s", reminder.text)
        await events.publish(
            REMINDER_DUE_EVENT,
            {"id": reminder.id, "text": reminder.text, "due_at": reminder.due_at},
        )
    return due


def _applescript_quote(text: str) -> str:
    """Make text safe to sit inside an AppleScript double-quoted string."""
    flattened = " ".join(text.split())  # No newlines — they'd break the script.
    return flattened.replace("\\", "\\\\").replace('"', '\\"')


async def _mac_notification(payload: Any) -> None:
    """Pop a macOS desktop notification. Quietly does nothing elsewhere.

    Safety note: this never runs a shell, and never executes user text. The
    reminder text is escaped and embedded in a fixed AppleScript snippet passed
    to `osascript` as a plain argument.
    """
    if sys.platform != "darwin" or not isinstance(payload, dict):
        return
    text = _applescript_quote(str(payload.get("text", ""))[:200])
    script = f'display notification "{text}" with title "Nova reminder"'
    try:
        process = await asyncio.create_subprocess_exec(
            "osascript",
            "-e",
            script,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()
    except OSError:
        logger.warning("Could not show a desktop notification.", exc_info=True)


class RemindersPlugin(Plugin):
    """Wires up the reminder commands, storage, and the due-checker loop."""

    name = "reminders"
    version = "0.1.0"
    description = "Reminders with times: save, list, complete, and get notified when due."

    #: How often the background loop checks for due reminders.
    check_interval_seconds: float = 15.0

    def __init__(self) -> None:
        self._store: ReminderStore | None = None
        self._events: EventBus | None = None
        self._watch_task: asyncio.Task[None] | None = None

    def _store_path(self, context: NovaContext) -> Path:
        """Keep reminders.json next to memory.json (respects the memory path setting)."""
        from nova.memory.manager import default_memory_path

        memory_setting = context.settings.memory.path
        memory_path = Path(memory_setting) if memory_setting else default_memory_path()
        return memory_path.parent / "reminders.json"

    async def setup(self, context: NovaContext) -> None:
        self._store = ReminderStore(self._store_path(context))
        self._events = context.events

        context.commands.register(RemindMeCommand(self._store))
        context.commands.register(ListRemindersCommand(self._store))
        context.commands.register(CompleteReminderCommand(self._store))

        context.events.subscribe(REMINDER_DUE_EVENT, _mac_notification)
        self._watch_task = asyncio.create_task(self._watch())

    async def teardown(self, context: NovaContext) -> None:
        if self._watch_task is not None:
            self._watch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._watch_task
            self._watch_task = None
        context.events.unsubscribe(REMINDER_DUE_EVENT, _mac_notification)

    async def _watch(self) -> None:
        """Forever: sleep a little, then announce anything newly due."""
        assert self._store is not None and self._events is not None
        while True:
            await asyncio.sleep(self.check_interval_seconds)
            try:
                await check_due_reminders(self._store, self._events)
            except Exception:  # noqa: BLE001 - the loop must survive one bad sweep.
                logger.exception("Reminder check failed; will try again.")

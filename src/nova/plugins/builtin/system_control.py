"""Focused, safe system checks: battery, disk space, and looking inside folders.

The `system` plugin answers "how is the whole machine doing?" with one big
snapshot. This plugin adds small, single-question checks the AI can reach for
directly ("how much battery is left?"), plus a safe way to list a folder.

SECURITY DESIGN — read this before adding commands here:
  * No shell, no subprocess. Every answer comes from Python APIs (psutil,
    pathlib). There is no command string anywhere, so there is nothing a user
    could type that gets executed.
  * Fixed questions, not free-form ones. Each command answers exactly ONE
    question, so there is no command name or flag to sanitize in the first
    place. Do NOT add a "run this command" command to this file.
  * Folder listing is sandboxed: paths are fully resolved (symlinks and `..`
    included) and must stay inside your home folder, and private folders like
    ~/.ssh are refused outright. Everything is read-only.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psutil

from nova.commands.base import Command
from nova.plugins.base import Plugin

if TYPE_CHECKING:
    from nova.context import NovaContext

# Folders inside home that hold secrets (keys, tokens). We refuse to even list
# their names — Nova has no business in them, and an AI mistake shouldn't
# expose what's there.
BLOCKED_DIR_NAMES = frozenset({".ssh", ".aws", ".gnupg", ".kube", ".docker"})

# Cap how many entries one listing returns, so a huge folder can't flood the
# AI's context (or the chat) with thousands of lines.
MAX_ENTRIES = 100


def _has_blocked_part(path: Path) -> bool:
    """True if any path component names a private folder (case-insensitive)."""
    return any(part.lower() in BLOCKED_DIR_NAMES for part in path.parts)


def _describe_battery() -> dict[str, Any]:
    """Read the battery via psutil. Runs in a worker thread."""
    battery = psutil.sensors_battery()
    if battery is None:
        return {
            "has_battery": False,
            "note": "No battery found — this machine is likely a desktop or a VM.",
        }

    result: dict[str, Any] = {
        "has_battery": True,
        "percent": round(battery.percent),
        "plugged_in": bool(battery.power_plugged),
    }

    # secsleft is a countdown to empty. psutil uses special markers for
    # "plugged in / not draining" and "still calculating".
    if battery.secsleft == psutil.POWER_TIME_UNLIMITED:
        result["time_left"] = "unlimited (plugged in)"
    elif battery.secsleft == psutil.POWER_TIME_UNKNOWN or battery.secsleft < 0:
        result["time_left"] = "unknown"
    else:
        hours, minutes = divmod(battery.secsleft // 60, 60)
        result["time_left"] = f"{hours}h {minutes}m"
    return result


def _describe_disk() -> dict[str, Any]:
    """Read main-disk usage via psutil. Runs in a worker thread."""
    usage = psutil.disk_usage(str(Path.home()))
    return {
        "total_gb": round(usage.total / 1e9, 1),
        "used_gb": round(usage.used / 1e9, 1),
        "free_gb": round(usage.free / 1e9, 1),
        "used_percent": usage.percent,
    }


def resolve_safe_folder(raw: str) -> Path | str:
    """Turn user input into a folder Path that is PROVABLY inside home.

    Returns the resolved Path on success, or a human-readable refusal string.
    Order matters: we resolve FIRST (following symlinks and collapsing `..`),
    then check the final real location — so a symlink pointing outside home,
    or a path like `~/Desktop/../../..`, is judged by where it actually lands.
    """
    home = Path.home().resolve()

    if not raw.strip():
        candidate: Path = home
    else:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            # Relative paths are taken relative to home, e.g. "Desktop/school".
            candidate = home / candidate

    # Refuse private folders BEFORE checking existence, so the answer doesn't
    # even reveal whether e.g. ~/.ssh exists on this machine. Compare
    # case-INSENSITIVELY: macOS's default filesystem is case-insensitive, so
    # "~/.SSH" reaches the real ~/.ssh and must be blocked just the same.
    if _has_blocked_part(candidate):
        return "That folder holds private keys or credentials, so Nova won't list it."

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return f"No such folder: {raw}"
    except ValueError:
        # e.g. an embedded null byte in the path — treat as a bad request.
        return "That doesn't look like a valid folder path."
    except OSError as exc:
        return f"Could not open that folder: {type(exc).__name__}"

    if resolved != home and home not in resolved.parents:
        return "That folder is outside your home folder, which Nova won't touch."

    # Re-check after resolving: a symlink could point INTO a blocked folder.
    if _has_blocked_part(resolved):
        return "That folder holds private keys or credentials, so Nova won't list it."

    if not resolved.is_dir():
        return f"That path is a file, not a folder: {raw}"

    return resolved


def _list_folder(raw: str) -> dict[str, Any]:
    """List a folder's contents (after the safety checks). Runs in a worker thread."""
    resolved = resolve_safe_folder(raw)
    if isinstance(resolved, str):
        return {"error": resolved}

    try:
        children = sorted(resolved.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        return {"error": "Nova doesn't have permission to read that folder."}
    except OSError:
        # The folder existed a moment ago but was deleted/renamed since the
        # safety check (a rare race) — fail gracefully, not with a crash.
        return {"error": "That folder is no longer available."}

    entries: list[dict[str, Any]] = []
    for child in children[:MAX_ENTRIES]:
        entry: dict[str, Any] = {"name": child.name}
        try:
            # lstat = "describe the entry itself" (a symlink is reported as a
            # link, not silently followed to wherever it points).
            stat = child.lstat()
            if child.is_symlink():
                entry["type"] = "link"
            elif child.is_dir():
                entry["type"] = "folder"
            else:
                entry["type"] = "file"
                entry["size_kb"] = round(stat.st_size / 1024, 1)
            # Show the time on the user's own wall clock, with its zone label,
            # so "modified 14:30 EDT" isn't misread as a UTC time.
            local_mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC).astimezone()
            entry["modified"] = local_mtime.strftime("%Y-%m-%d %H:%M %Z")
        except OSError:
            entry["type"] = "unreadable"
        entries.append(entry)

    result: dict[str, Any] = {
        "folder": str(resolved),
        "total_entries": len(children),
        "entries": entries,
    }
    if len(children) > MAX_ENTRIES:
        result["note"] = f"Folder has {len(children)} entries; showing the first {MAX_ENTRIES}."
    return result


class BatteryCommand(Command):
    """How charged the battery is right now."""

    name = "battery"
    description = (
        "Check the battery: percent charged, whether it's plugged in, and time "
        "remaining. Use when asked about battery or charge level."
    )

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(_describe_battery)


class DiskSpaceCommand(Command):
    """How full the main disk is."""

    name = "disk_space"
    description = (
        "Check free and used space on the main disk. Use when asked about disk "
        "space, storage, or whether the drive is getting full."
    )

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(_describe_disk)


class ListFilesCommand(Command):
    """What's inside a folder (home folder only)."""

    name = "list_files"
    description = (
        "List the files and folders inside a folder in the user's home "
        "directory (e.g. '~/Desktop' or 'Documents/school'). Read-only; "
        "refuses anything outside home and private folders like ~/.ssh."
    )
    parameters = {
        "type": "object",
        "properties": {
            "folder": {
                "type": "string",
                "description": (
                    "The folder to list. Accepts '~' paths or paths relative to "
                    "home. Default: the home folder itself."
                ),
            },
        },
    }

    async def run(self, args: dict[str, Any]) -> dict[str, Any]:
        # `or "~"` (not a get-default) so an explicit null/empty from the LLM
        # still means "the home folder", never the literal path "None".
        folder = str(args.get("folder") or "~")
        return await asyncio.to_thread(_list_folder, folder)


class SystemControlPlugin(Plugin):
    """Registers the focused system-check commands."""

    name = "system-control"
    version = "0.1.0"
    description = "Safe, focused system checks: battery, disk space, and folder listing."

    async def setup(self, context: NovaContext) -> None:
        context.commands.register(BatteryCommand())
        context.commands.register(DiskSpaceCommand())
        context.commands.register(ListFilesCommand())

"""Test the system-control plugin: sane data out, and the folder sandbox holds."""

from __future__ import annotations

from pathlib import Path

import pytest

from nova.plugins.builtin.system_control import (
    BatteryCommand,
    DiskSpaceCommand,
    ListFilesCommand,
    resolve_safe_folder,
)
from nova.plugins.manager import PluginManager


def test_discovery_finds_system_control() -> None:
    names = [cls.name for cls in PluginManager().discover()]
    assert "system-control" in names


async def test_battery_reports_something_sane() -> None:
    result = await BatteryCommand().run({})

    assert isinstance(result["has_battery"], bool)
    if result["has_battery"]:
        assert 0 <= result["percent"] <= 100
        assert isinstance(result["plugged_in"], bool)


async def test_disk_space_is_sane() -> None:
    result = await DiskSpaceCommand().run({})

    assert result["total_gb"] > 0
    assert result["free_gb"] >= 0
    assert 0 <= result["used_percent"] <= 100


async def test_list_files_shows_home_by_default() -> None:
    result = await ListFilesCommand().run({})

    assert result["folder"] == str(Path.home().resolve())
    assert isinstance(result["entries"], list)


async def test_list_files_handles_missing_folder() -> None:
    result = await ListFilesCommand().run({"folder": "~/definitely-not-a-real-folder-xyz"})
    assert "error" in result


async def test_list_files_null_folder_means_home() -> None:
    # LLMs often pass an explicit null for optional params; that must mean
    # "home", never the literal path "None".
    result = await ListFilesCommand().run({"folder": None})
    assert result.get("folder") == str(Path.home().resolve())


async def test_list_files_survives_null_byte() -> None:
    result = await ListFilesCommand().run({"folder": "bad\x00path"})
    assert "error" in result  # graceful refusal, not a crash


async def test_list_files_refuses_paths_outside_home() -> None:
    for sneaky in ["/etc", "/", "~/../..", "Desktop/../../../etc"]:
        result = await ListFilesCommand().run({"folder": sneaky})
        assert "error" in result, f"expected {sneaky!r} to be refused"


async def test_list_files_refuses_private_folders() -> None:
    # These may not exist on every machine; either refusal message is fine,
    # but they must NEVER return a listing.
    for private in ["~/.ssh", "~/.aws", "~/.ssh/keys"]:
        result = await ListFilesCommand().run({"folder": private})
        assert "error" in result, f"expected {private!r} to be refused"


def _fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point resolve_safe_folder's notion of 'home' at a throwaway folder."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


def test_private_folder_blocked_case_insensitively(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """~/.SSH must be refused too — macOS filesystems are case-insensitive."""
    home = _fake_home(tmp_path, monkeypatch)
    (home / ".ssh").mkdir()
    for variant in ["~/.ssh", "~/.SSH", "~/.Ssh"]:
        verdict = resolve_safe_folder(variant)
        assert isinstance(verdict, str), f"{variant!r} should be refused, got {verdict!r}"
        assert "private" in verdict


def test_symlink_into_private_folder_is_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlink whose real target is a blocked folder must still be refused."""
    home = _fake_home(tmp_path, monkeypatch)
    (home / ".aws").mkdir()
    link = home / "shortcut"
    try:
        link.symlink_to(home / ".aws")
    except OSError:
        pytest.skip("cannot create symlinks in this environment")
    verdict = resolve_safe_folder(str(link))
    assert isinstance(verdict, str) and "private" in verdict


def test_symlink_escaping_home_is_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlink inside home pointing outside home must be refused."""
    home = _fake_home(tmp_path, monkeypatch)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = home / "escape"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("cannot create symlinks in this environment")
    verdict = resolve_safe_folder(str(link))
    assert isinstance(verdict, str) and "outside your home" in verdict

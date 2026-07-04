"""Test that settings load correctly and layer in the right priority order.

Priority (highest first): environment variables > config.yaml > built-in defaults.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nova.core.config import Settings, load_settings


def test_built_in_defaults() -> None:
    settings = Settings()
    assert settings.server.port == 8000
    assert settings.ai.provider == "ollama"
    assert settings.memory.backend == "json"


def test_env_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    # Note the DOUBLE underscore between the section and the key.
    monkeypatch.setenv("NOVA_SERVER__PORT", "9999")
    monkeypatch.setenv("NOVA_AI__PROVIDER", "anthropic")

    settings = Settings()
    assert settings.server.port == 9999
    assert settings.ai.provider == "anthropic"


def test_yaml_file_and_env_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  port: 7000\nai:\n  provider: anthropic\n")
    monkeypatch.setenv("NOVA_CONFIG_FILE", str(config_file))

    # With only the YAML file, its values win over defaults.
    settings = load_settings()
    assert settings.server.port == 7000
    assert settings.ai.provider == "anthropic"

    # Now an env var should beat the YAML file.
    monkeypatch.setenv("NOVA_SERVER__PORT", "7500")
    settings = load_settings()
    assert settings.server.port == 7500
    assert settings.ai.provider == "anthropic"  # still from YAML

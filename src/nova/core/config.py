"""Nova's settings ("configuration").

A big idea here: settings can come from THREE places, and later ones can be
overridden by earlier ones (highest priority first):

  1. Environment variables   (great for secrets like API keys)
  2. config/config.yaml       (a friendly file you can edit by hand)
  3. Built-in defaults        (sensible fallbacks so Nova runs out of the box)

We group related settings so it's tidy: `settings.ai.model`, `settings.server.port`,
and so on. `pydantic` checks every value has the right type, and yells early if not.

Environment variable naming (note the DOUBLE underscore between section and key):
    NOVA_SERVER__PORT=9000
    NOVA_AI__PROVIDER=anthropic
    NOVA_AI__ANTHROPIC_API_KEY=sk-...

To point at a different YAML file, set NOVA_CONFIG_FILE=/path/to/file.yaml
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

DEFAULT_CONFIG_FILE = "config/config.yaml"


class ServerSettings(BaseModel):
    """Where and how the web server runs."""

    host: str = "127.0.0.1"  # "127.0.0.1" = only this computer can reach it.
    port: int = 8000
    reload: bool = False  # Auto-restart on code changes (handy while developing).


class AISettings(BaseModel):
    """Which AI "brain" Nova uses, and its options."""

    provider: str = "ollama"  # "ollama" (local) or "anthropic" (cloud Claude).
    temperature: float = 0.7  # 0 = focused/predictable, 1 = creative.
    max_tokens: int = 1024  # Rough cap on how long a reply can be.

    # --- Local (Ollama) options ---
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # --- Cloud (Anthropic Claude) options ---
    # The key is intentionally left empty here — set it via the environment
    # (NOVA_AI__ANTHROPIC_API_KEY) so secrets never get committed to git.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"


class MemorySettings(BaseModel):
    """How Nova remembers things."""

    backend: str = "json"  # Only "json" exists today; more can be added later.
    # Where to store the memory file. None = a sensible per-user app-data folder.
    path: str | None = None


class VoiceSettings(BaseModel):
    """Speech-to-text (listening) and text-to-speech (speaking) engine choices."""

    stt_engine: str = "placeholder"  # Real engines (e.g. Whisper) come later.
    tts_engine: str = "placeholder"  # Real engines (e.g. Piper) come later.


class LoggingSettings(BaseModel):
    """How chatty Nova's logs are, and their format."""

    level: str = "INFO"  # DEBUG | INFO | WARNING | ERROR
    json_format: bool = False  # True = machine-readable JSON logs.


class Settings(BaseSettings):
    """The full settings object, grouping every section above."""

    model_config = SettingsConfigDict(
        env_prefix="NOVA_",  # All Nova env vars start with NOVA_.
        env_nested_delimiter="__",  # Use __ to reach into a section (AI__PROVIDER).
        env_file=".env",  # Also read a local .env file if present.
        extra="ignore",  # Ignore unknown keys instead of crashing.
    )

    server: ServerSettings = Field(default_factory=ServerSettings)
    ai: AISettings = Field(default_factory=AISettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Decide the priority order of where settings come from.

        Order matters: the first source wins when the same value is set twice.
        We put environment variables ABOVE the YAML file, so a deployed server
        can override the committed config without editing files.
        """
        sources: list[PydanticBaseSettingsSource] = [
            init_settings,  # Values passed directly in code (highest priority).
            env_settings,  # Environment variables.
            dotenv_settings,  # A .env file.
        ]

        config_file = Path(os.environ.get("NOVA_CONFIG_FILE", DEFAULT_CONFIG_FILE))
        if config_file.is_file():
            sources.append(
                YamlConfigSettingsSource(settings_cls, yaml_file=config_file)
            )

        sources.append(file_secret_settings)  # Docker/K8s "secret files" (rarely used).
        return tuple(sources)


def load_settings() -> Settings:
    """Build the settings object. Call this once at startup.

    Tip: set NOVA_CONFIG_FILE beforehand to load a different YAML file
    (useful in tests).
    """
    return Settings()

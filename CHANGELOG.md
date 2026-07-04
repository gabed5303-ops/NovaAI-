# Changelog

All notable changes to Nova are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project uses [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-07-04

Nova gets a **face and a storefront**: a full website with a chat app.

### Added
- **Chat web UI** at `/chat` — a ChatGPT-style page (message bubbles, typing
  indicator, quick-start suggestions, dark theme) served straight from FastAPI
  with zero build step.
- **Website homepage** at `/` — hero, features grid, how-it-works, Free/Pro
  pricing section (Pro is honestly labeled "coming soon"), and footer.
- Configurable **system prompt** (`ai.system_prompt`) so the assistant
  introduces itself as Nova when no system message is supplied.
- Tests for the homepage and chat page.

### Changed
- Distribution renamed `nova` → `nova-assistant` (the old name collided with
  OpenStack Nova on PyPI and triggered dozens of false Dependabot alerts).
  The import package and the `nova` CLI command are unchanged.

## [0.2.0] - 2026-07-04

The **GitHub-ready** release: same solid foundation, now packaged as a proper
open-source project.

### Added
- `SECURITY.md` — how to report vulnerabilities privately.
- `CONTRIBUTING.md` — how to set up the project and propose changes.
- `CODE_OF_CONDUCT.md` — community guidelines (Contributor Covenant).
- GitHub issue templates (bug report, feature request) and a pull-request template.
- Dependabot config — automatic dependency and GitHub Actions security updates.
- `CHANGELOG.md` — this file.
- README badges and Security/Contributing pointers.

### Changed
- Commit identity uses a privacy-preserving GitHub `noreply` email so no personal
  email address is exposed publicly.

## [0.1.0] - 2026-07-03

The initial **foundation**: a clean, layered, runnable skeleton.

### Added
- Layered architecture under `src/nova/` (core, ai, memory, voice, commands,
  plugins, api) with a single composition root (`context.py`).
- FastAPI backend with endpoints for health, chat, memory, voice, plugins, and
  commands.
- AI providers behind one interface: Ollama (local) and Anthropic Claude (cloud).
- Memory system with a default JSON-file backend.
- Voice module with placeholder speech-to-text and text-to-speech engines.
- Plugin system with built-in + entry-point discovery, plus an example `hello`
  plugin.
- Layered configuration (environment variables > `config.yaml` > defaults).
- Tooling: uv, ruff, mypy, pytest (16 tests), GitHub Actions CI, MIT license,
  and full README + architecture docs.

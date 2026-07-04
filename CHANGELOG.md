# Changelog

All notable changes to Nova are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project uses [Semantic Versioning](https://semver.org/).

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

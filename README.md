# Nova 🤖

[![CI](https://github.com/gabed5303-ops/NovaAI-/actions/workflows/ci.yml/badge.svg)](https://github.com/gabed5303-ops/NovaAI-/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Nova** is a modular, JARVIS-inspired AI assistant written in Python. It's built
to grow: clean architecture, a plugin system, memory, voice, and support for both
local and cloud AI models — all behind tidy, swappable interfaces.

> This repository currently contains the **foundation**: a working, well-documented
> skeleton you can run today and build features on for years. Voice is a placeholder
> for now; everything is wired end-to-end.

---

## ✨ What's inside

| Capability | Status | Where |
|---|---|---|
| Web backend (FastAPI) | ✅ working | `src/nova/api/` |
| Configuration (YAML + env) | ✅ working | `src/nova/core/config.py` |
| Plugin system | ✅ working | `src/nova/plugins/` |
| Command system | ✅ working | `src/nova/commands/` |
| Memory (JSON file) | ✅ working | `src/nova/memory/` |
| Local AI (Ollama) | ✅ working | `src/nova/ai/ollama_provider.py` |
| Cloud AI (Anthropic Claude) | ✅ working (optional) | `src/nova/ai/anthropic_provider.py` |
| Voice (STT + TTS) | 🟡 placeholder | `src/nova/voice/` |
| Event bus | ✅ working | `src/nova/core/events.py` |

---

## 🚀 Quick start

You need [**uv**](https://docs.astral.sh/uv/) (a fast Python project manager) and
Python 3.11+.

```bash
# 1. Install everything into a local environment
uv sync

# 2. (Optional) create your own settings and secrets files
cp config/config.example.yaml config/config.yaml
cp .env.example .env

# 3. Run the tests to confirm it all works
uv run pytest

# 4. Start Nova
uv run nova
```

Then open **http://127.0.0.1:8000/docs** — FastAPI gives you an interactive page
to try every endpoint. Or use `curl`:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/plugins
curl -X POST http://127.0.0.1:8000/commands/hello -H "Content-Type: application/json" -d '{"args":{"name":"Ada"}}'
```

---

## 🧠 Talking to an AI model

**Local (default) — Ollama:** install [Ollama](https://ollama.com), then:

```bash
ollama pull llama3          # download a model once
# make sure Ollama is running, then:
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message":"Hello!"}'
```

**Cloud — Anthropic Claude:** install the optional extra and set your key.

```bash
uv sync --extra cloud
export NOVA_AI__PROVIDER=anthropic
export NOVA_AI__ANTHROPIC_API_KEY=sk-ant-...
uv run nova
```

If a model isn't reachable, `/chat` returns a clear **503** message instead of
crashing.

---

## 🗂️ Project layout — every component explained

```
Nova/
├── pyproject.toml          # Project info + dependencies + tool settings.
├── config/                 # Human-editable settings files.
│   └── config.example.yaml # Copy to config.yaml to customize (git-ignored).
├── docs/ARCHITECTURE.md    # Deeper "how it fits together" guide.
├── tests/                  # Automated tests proving Nova works.
└── src/nova/
    ├── main.py             # The on/off switch: starts the web server.
    ├── context.py          # The control center: builds & holds every service.
    │
    ├── core/               # Foundation everything else stands on:
    │   ├── config.py        #   settings (defaults → config.yaml → env vars)
    │   ├── logging.py       #   nice, adjustable log messages
    │   ├── events.py        #   an internal "announcement system" (event bus)
    │   └── exceptions.py    #   Nova's own error types
    │
    ├── ai/                 # The AI "brains":
    │   ├── base.py          #   the contract every brain follows (LLMProvider)
    │   ├── schemas.py       #   the shape of chat messages & replies
    │   ├── registry.py      #   picks the brain from your settings
    │   ├── ollama_provider.py     #   local brain
    │   └── anthropic_provider.py  #   cloud brain (Claude)
    │
    ├── memory/             # How Nova remembers things:
    │   ├── base.py          #   the storage contract (MemoryStore)
    │   ├── models.py        #   the shape of one memory
    │   ├── manager.py       #   friendly front desk (remember / recall / forget)
    │   └── backends/json_store.py  #   default: a simple JSON file
    │
    ├── voice/              # Ears & mouth (placeholders for now):
    │   ├── base.py          #   contracts (SpeechToText, TextToSpeech)
    │   ├── stt.py           #   placeholder listener
    │   ├── tts.py           #   placeholder speaker
    │   └── manager.py       #   bundles them: listen() / speak()
    │
    ├── commands/           # Individual actions Nova can do:
    │   ├── base.py          #   what a Command is
    │   └── registry.py      #   the "phone book" of commands
    │
    ├── plugins/            # How Nova gains new abilities:
    │   ├── base.py          #   what a Plugin is
    │   ├── manager.py       #   finds & loads plugins (built-in + installed)
    │   └── builtin/hello.py #   example plugin adding the `hello` command
    │
    └── api/                # The web "front door" (thin — no real logic):
        ├── app.py           #   builds the FastAPI app; startup/shutdown wiring
        ├── deps.py          #   lets routes reach the services
        ├── schemas.py       #   request/response shapes
        └── routes/          #   one file per feature (health, chat, memory, ...)
```

For the reasoning behind these choices, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## 🔌 Writing your own plugin

A plugin teaches Nova new commands. Copy `src/nova/plugins/builtin/hello.py` as a
template:

```python
from nova.commands.base import Command
from nova.plugins.base import Plugin


class PingCommand(Command):
    name = "ping"
    description = "Replies with pong."

    async def run(self, args):
        return {"reply": "pong"}


class PingPlugin(Plugin):
    name = "ping"
    version = "0.1.0"
    description = "Adds a ping command."

    async def setup(self, context):
        context.commands.register(PingCommand())
```

Drop that file in `src/nova/plugins/builtin/` and it's discovered automatically on
the next start. (Third-party plugins can be published as packages using the
`nova.plugins` entry-point group — see the architecture doc.)

---

## ⚙️ Configuration

Settings can come from three places (higher wins):

1. **Environment variables** — `NOVA_AI__PROVIDER=anthropic` (best for secrets).
2. **`config/config.yaml`** — friendly to edit; git-ignored so it stays local.
3. **Built-in defaults** — so Nova runs with no setup at all.

See `config/config.example.yaml` and `.env.example` for every available option.

---

## 🧪 Development

```bash
uv run pytest        # run the tests
uv run ruff check .  # check code style / tidy imports
uv run mypy src      # check types
```

GitHub Actions runs all three automatically on every push (see
`.github/workflows/ci.yml`).

---

## 🤝 Contributing & security

- New here? Start with **[CONTRIBUTING.md](CONTRIBUTING.md)**.
- Please follow our **[Code of Conduct](CODE_OF_CONDUCT.md)**.
- Found a security issue? See **[SECURITY.md](SECURITY.md)** — report it
  privately, never in a public issue.
- Changes are tracked in **[CHANGELOG.md](CHANGELOG.md)**.

---

## 🗺️ Roadmap (next foundations to build on)

- Real speech-to-text (e.g. Whisper) and text-to-speech (e.g. Piper).
- A database / vector memory backend for smarter recall.
- Streaming chat responses.
- A live voice loop (wake word → listen → think → speak) using the event bus.
- Authentication for remote access.

---

## 📄 License

[MIT](LICENSE) — free to use, change, and share.

# Nova Architecture

This document explains *how Nova is put together* and *why*. If the README is the
"what", this is the "how it fits".

## The big idea: layers

Nova is built in layers, like a cake. Lower layers know nothing about higher
layers. Dependencies only ever point **downward**. This is what keeps the project
easy to change: you can replace a higher layer (say, the web API) without
touching the lower ones.

```
        ┌─────────────────────────────────────────────┐
        │  main.py         (the on/off switch)         │   entrypoint
        └───────────────────────┬─────────────────────┘
                                │ starts
        ┌───────────────────────▼─────────────────────┐
        │  api/            (the web "front door")      │   transport layer
        │  routes: health, chat, memory, voice,        │   (thin! no logic)
        │          plugins, commands                   │
        └───────────────────────┬─────────────────────┘
                                │ uses (via NovaContext)
        ┌───────────────────────▼─────────────────────┐
        │  context.py    (control center / wiring)     │   composition root
        └───────────────────────┬─────────────────────┘
                                │ builds & holds
   ┌────────────┬───────────────┼───────────────┬──────────────┐
   ▼            ▼               ▼               ▼              ▼
┌──────┐   ┌────────┐     ┌─────────┐    ┌──────────┐   ┌──────────┐
│  ai  │   │ memory │     │  voice  │    │ commands │   │ plugins  │   feature modules
└──┬───┘   └───┬────┘     └────┬────┘    └────┬─────┘   └────┬─────┘
   │           │               │              │              │
   └───────────┴───────────────┴──────────────┴──────────────┘
                                │ all use
        ┌───────────────────────▼─────────────────────┐
        │  core/   config · logging · events · errors  │   foundation
        └─────────────────────────────────────────────┘
```

## The three patterns you'll see everywhere

1. **Interface first, implementation second (dependency inversion).**
   Every capability that touches the outside world is defined as an abstract
   "contract" (an `ABC`) before any concrete version exists:
   - `ai/base.py` → `LLMProvider`   (implemented by Ollama, Anthropic)
   - `memory/base.py` → `MemoryStore` (implemented by the JSON store)
   - `voice/base.py` → `SpeechToText`, `TextToSpeech` (implemented by placeholders)

   The rest of Nova depends on the *contract*, never the concrete class. That's
   how "local or cloud AI" and "swap the memory backend" become one-line config
   changes instead of rewrites.

2. **A registry/factory chooses the implementation.**
   Files like `ai/registry.py`, `memory/manager.py`, and `voice/manager.py` are
   the *only* places that know each concrete class by name. They read your
   settings and build the right one. Add a new implementation → edit one factory.

3. **One composition root (`context.py`).**
   Everything is built once, in dependency order, inside `build_context()`, and
   stored in a single `NovaContext`. No global variables, no hidden state. Tests
   build their own context with test settings — total isolation.

## How a request flows (example: running the `hello` command)

```
HTTP POST /commands/hello
  → api/routes/commands.py         (reads the request)
  → get_context() dependency        (grabs the NovaContext)
  → context.commands.run("hello")   (CommandRegistry finds the command)
  → HelloCommand.run(args)          (the plugin's code does the work)
  → JSON response back to the caller
```

The command only exists because, at startup:

```
build_context()
  → PluginManager.load_all(context)
  → discovers HelloPlugin (in plugins/builtin/hello.py)
  → HelloPlugin.setup(context)
  → context.commands.register(HelloCommand())
```

## Settings priority

Settings come from three places. Higher on this list wins:

1. Environment variables (e.g. `NOVA_AI__PROVIDER=anthropic`) — best for secrets.
2. `config/config.yaml` — friendly, human-editable, but git-ignored so it stays local.
3. Built-in defaults in `core/config.py` — so Nova runs with zero configuration.

## Why these choices (short version)

- **`src/` layout** — tests run against the installed package, not loose files;
  prevents a whole class of "works on my machine" import bugs.
- **Async everywhere** — a voice assistant spends most of its time waiting on
  I/O (models, mics, network). Async lets it do other things while it waits.
- **Event bus (`core/events.py`)** — lets modules react to each other ("on command
  complete") without being wired together directly. Reserved for future
  JARVIS-style behaviors.
- **Entry-point plugin discovery** — a third party can publish `nova-weather` on
  PyPI and users get it just by installing it. No core changes.

## What's deliberately NOT here yet

Real speech engines, a vector/database memory backend, authentication,
websockets/a live voice loop, and streaming chat. Every one of these has an
interface already reserved, so it slots in without reworking the foundation.

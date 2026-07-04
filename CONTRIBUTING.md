# Contributing to Nova

Thanks for your interest in Nova! This guide gets you from zero to a working
setup, and explains how to propose changes.

## Getting set up

You need [**uv**](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
# 1. Fork this repo on GitHub, then clone your fork:
git clone https://github.com/<your-username>/NovaAI-.git
cd NovaAI-

# 2. Install everything (creates a local virtual environment automatically):
uv sync

# 3. Confirm it works:
uv run pytest
```

## The workflow

1. **Make a branch** for your change:
   ```bash
   git checkout -b my-feature
   ```
2. **Make your change.** Keep it focused — one idea per pull request.
3. **Run the checks** before you commit:
   ```bash
   uv run ruff check .   # code style + tidy imports
   uv run mypy src       # type checking
   uv run pytest         # tests
   ```
4. **Commit and push** to your fork, then open a **Pull Request** on GitHub.

The CI robot (GitHub Actions) runs the same three checks on your PR
automatically.

## Style

- Match the surrounding code — clear names, short functions, comments that
  explain *why*.
- New behavior should come with a test in `tests/`.
- If you add a dependency, add it with `uv add <name>` so `pyproject.toml` and
  the lockfile stay in sync.

## Adding a plugin (the fun part)

Nova is built to be extended. The quickest way to add a feature is a plugin —
copy `src/nova/plugins/builtin/hello.py` as a template. See the README section
"Writing your own plugin" and `docs/ARCHITECTURE.md` for how it all fits.

## Never commit secrets

API keys and personal data must never be committed. Put them in a local `.env`
file (already git-ignored). See `SECURITY.md`.

## Code of Conduct

By participating, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

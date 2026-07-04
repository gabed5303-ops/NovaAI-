# Security Policy

Thanks for helping keep Nova and its users safe.

## Reporting a vulnerability

**Please do NOT open a public issue for security problems.** Public issues are
visible to everyone, which could put users at risk before a fix exists.

Instead, report privately using GitHub's built-in tool:

1. Go to the **Security** tab of this repository.
2. Click **Report a vulnerability** (this opens a private advisory only the
   maintainers can see).
3. Describe the problem, how to reproduce it, and the impact.

We aim to acknowledge reports within a few days and will keep you updated on the
fix.

## Good security habits for this project

Nova is built so that secrets never end up in the code or on GitHub:

- **API keys and secrets go in environment variables or a local `.env` file**,
  never in the code. The `.env` file is ignored by git (see `.gitignore`).
- **`config/config.yaml` is git-ignored** — only the safe `config.example.yaml`
  template is shared.
- If you ever think you committed a secret by accident: rotate (replace) that
  secret immediately, then remove it from the repository history.

## Supported versions

This project is in early development. Security fixes are applied to the latest
release on the `main` branch.

# Tools and writing

## Course materials and external writing

Use [Clarity](../skills/clarity/SKILL.md) and its relevant mode references for
course materials, documentation, articles, slides, captions, and other
reader-facing assets. Preserve Mark's voice, source attribution, and factual
limits. Do not invent personal experience or supporting facts. Apply the same
requirements to delegated work when delegation is authorized.

## Developer credentials

Use [1Password Environments](../skills/1password-environments/SKILL.md) for
authorized developer credential and environment work. Inspect variable names
through its MCP tools; never print secret values or read a mounted `.env` to
verify it. Resolve the intended account and environment instead of copying IDs.
Installing a skill does not authorize creating secrets, mounts, or accounts.

The workshop itself must run without developer credentials or 1Password.

## Project configuration

Maintain development MCP definitions and plugin preferences in
`.codex/config.toml`. Keep executable launchers under `scripts/dev/` and resolve
them within this checkout. Do not edit HQ or global Codex settings to configure
this workshop. Do not add developer-tool startup to Compose, the devcontainer,
Python requirements, notebooks, workshop tests, or participant instructions.

See [developer setup](../../docs/development-agent-setup.md) for local
prerequisites and source provenance. Plugin availability, project trust, and
account authorization remain local settings; they are not supplied by this repo.

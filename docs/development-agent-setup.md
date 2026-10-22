# Agent setup for workshop development

This is the maintainer's setup for building the workshop. Participants use the
workshop's own environment and instructions. They do not need Codex, HQ access,
1Password, Kata, Asana, or the plugins listed here.

## What is included

| Location | Development purpose |
| --- | --- |
| `AGENTS.md` | Workshop boundaries, code map, working rules, and checks |
| `.agents/references/` | Writing, credentials, review, and continuity guidance |
| `.agents/skills/clarity/` | Writing skill, references, examples, and package validator |
| `.agents/skills/1password-environments/` | Optional developer credential management |
| `.agents/skills/kata/`, `.kata.toml` | Optional, isolated local task tracking |
| `.codex/config.toml` | Project MCP definitions and development plugin preferences |
| `scripts/dev/` | Developer launchers and setup validation |

These files are ordinary copies in this repo. They need no sibling HQ checkout,
submodule, private download, or absolute source path. Keep future participant
agent skills separate from `.agents/skills/` so exercises do not load company
development instructions.

## Codex on a development machine

1. Open this repository in Codex and trust it when prompted. Start a fresh chat
   to load the repository instructions and project settings.
2. Check the Plugins screen for the declared packages. Plugin preferences do not
   install unavailable packages or authorize account connections. This setup
   inherits your model and permission settings.
3. If using the local Node REPL or 1Password MCP server, check executable discovery:

   ```sh
   ./scripts/dev/mcp-node-repl --check
   ./scripts/dev/mcp-1password --check
   ```

   These commands only check executables; they do not authenticate or start
   services. Launchers support PATH and the standard macOS locations used by HQ.
   For another installation, set `WORKSHOP_NODE_REPL_BIN` or
   `WORKSHOP_1PASSWORD_MCP_BIN` in the environment launching Codex. Paths must
   identify executable files. Desktop runtime/browser support and the 1Password
   desktop app still need to be installed for the corresponding tools.
4. Enable the 1Password MCP server in its desktop Developer settings and approve
   its client connection only when you want developer credential access. This
   setup creates no credentials or `.env` mounts. The authentication approval
   policy from HQ is preserved.
5. Run `codex mcp list` from the repository to inspect the configured server
   definitions. Listing them does not establish authentication or a working
   connection. Use the tool in a fresh chat when needed to verify the connection.

Plugin preferences cover browser control, visualization, office artifacts,
templates, Calendar, Slack, app tools, and code review. They are development
preferences, not workshop dependencies. HQ's Webflow connection is omitted.
No global settings, account permissions, Git hooks, or automations are installed.

Codex discovers repository skills under `.agents/skills/` and loads project
configuration for trusted projects. See the official
[skills documentation](https://learn.chatgpt.com/docs/build-skills) and
[configuration documentation](https://learn.chatgpt.com/docs/config-file/config-basic).

## Optional Kata

Use the existing Asana task for coordinated development. If local Kata continuity
is useful, install Kata separately and initialize this checkout's empty instance:

```sh
./scripts/dev/kata init --project semantic-contracts-workshop --agent
./scripts/dev/kata list --agent
```

Always use this wrapper. It selects `.kata/local/` and clears inherited server
and database routing. Do not import HQ's database or snapshot. No hook, snapshot,
or live database is copied into this repository. Local state stays ignored;
record durable decisions and verification in the related task or PR.

## Verify a change to this setup

With Python 3.11+ installed:

```sh
python3 scripts/dev/check-agent-setup.py
python3 .agents/skills/clarity/scripts/validate_package.py
sh -n scripts/dev/kata
sh -n scripts/dev/mcp-node-repl
sh -n scripts/dev/mcp-1password
git diff --check
```

The setup checker validates local configuration, required skill entrypoints,
instruction links, executable launchers, and references to developer tooling in
participant configuration. It uses only the standard library and does not
connect to services. Workshop runtime validation is a separate task; these checks
do not establish database, model, or exercise readiness.

## Source and maintenance

Adapted from `onthemarkdata/hq` at commit
`769ecf852993b71acf731d28494ee28d512e010a` on 21 October 2026.
The local skill and launcher source files were checked against the GitHub blob
hashes before copying. Clarity's MIT license and supporting files are retained;
1Password's skill retains its upstream attribution and metadata.

Changes from HQ are deliberate: workshop-specific instructions and launcher
paths, an independent optional Kata instance, no HQ Webflow connection, no copied
task records, and no dependency from participant startup to developer tools.
HQ policies inform this copy but are not fetched at runtime. Review future
updates before applying them; do not sync over workshop-specific boundaries or
the manual-only Tailscale policy.

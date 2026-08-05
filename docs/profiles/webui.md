# Profile: `webui`

The complete stack: visual DAG canvas, FastAPI backend, MCP server, all skills.

```bash
./install.sh --profile webui
```

## What this is for

You want to see pipelines as a graph, edit them by hand, and chat with an agent in the browser — with the canvas and the conversation staying in sync.

## What this is not for

- A machine without Node.js → use [`harness`](harness.md)
- No server at all → use [`skills`](skills.md)

## Prerequisites

- Python 3.10+ (3.10 recommended) in an activated venv or conda environment
- uv (the default Python package installer; use `--pip` as a fallback)
- Node.js 20+ with npm (recommended: [nvm](https://github.com/nvm-sh/nvm) — `nvm install 20`)
- At least one agent CLI, if you want the chat panel:
  - Claude Code: `curl -fsSL https://claude.ai/code/install.sh | sh`
  - Codex: `npm i -g @openai/codex`
  - Cursor: [download the IDE](https://cursor.com)

This project uses **npm**, not Yarn, despite a tracked `yarn.lock` — see [ADR-002](../architecture/adr-002-package-managers.md).

If `python3` resolves to an older Python, select a 3.10+ interpreter explicitly:

```bash
DATAFLOW_PYTHON="$(command -v python3.10)" ./install.sh --profile webui
```

## Install

```bash
./install.sh --profile webui --check      # prerequisites only
./install.sh --profile webui --dry-run    # print the plan
./install.sh --profile webui
# If uv is unavailable or disallowed:
./install.sh --profile webui --pip
```

Steps: install `open-dataflow` with uv → backend deps → `npm install` + `npm run build` → initialize the DataFlow core directory → render and install all skills. Pass `--pip` to use pip explicitly.

The frontend build is the slow part. It is skipped when `frontend/dist/index.html` already exists; delete that file to force a rebuild.

## Run

```bash
./scripts/start.sh              # foreground
./scripts/start.sh --daemon     # background
./scripts/start.sh --status
./scripts/start.sh --stop
```

Then open **http://localhost:8000/**. The backend serves both the canvas and the MCP endpoint. If you changed `DATAFLOW_PORT`, use that port.

There is **no authentication** — single-user local tool. `0.0.0.0` exposes it to your network; use `DATAFLOW_HOST=127.0.0.1` to keep it local.

## Connect an agent

```bash
./install.sh configure-agent --agent claude
./install.sh configure-agent --agent codex --scope user
./install.sh configure-agent --agent cursor
```

### Configuring Codex on Python 3.10

Editing `~/.codex/config.toml` requires parsing it first — the configurator will
not touch a file it cannot validate. Python 3.11+ has `tomllib` built in. On
3.10, install the declared dependency once:

```bash
pip install -r installers/requirements-configure.txt
```

Without it, `configure-agent --agent codex` refuses and prints the block to add
by hand. Claude and Cursor are unaffected — their configs are JSON.

### Auth

```bash
export ANTHROPIC_API_KEY=sk-ant-...          # Claude Code
export ANTHROPIC_BASE_URL=https://gateway/v1 # optional gateway

export OPENAI_API_KEY=sk-...                 # Codex, key mode
export OPENAI_BASE_URL=https://gateway/v1    # optional gateway
codex login                                  # Codex, OAuth mode (no key)
```

Export these in the shell that starts the backend — that is the environment the dispatched agent inherits. The installer never stores credentials.

### Two usage modes

**WebUI-dispatched** (Claude Code, Codex): the backend spawns the CLI headlessly when you chat in the browser. Pick the agent from the dropdown beside the chat title; switching starts a fresh session, and your choice persists across reloads.

**IDE-driven** (Cursor, or Claude Code in your terminal): you talk to the agent in your own environment and it pushes pipelines onto the canvas via MCP. Cursor also needs a one-time toggle: Settings → Features → MCP Servers → enable `dataflow`.

## Minimal verification

1. `./scripts/start.sh --status` reports running
2. `http://localhost:8000/` shows the canvas
3. In the chat panel: *"list the available operator categories"* — expect `core_text`, `general_text`, `reasoning`, …
4. Ask it to build a small pipeline; nodes should appear on the canvas

## Upgrade

```bash
git pull
rm -f frontend/dist/index.html      # force a frontend rebuild
./install.sh --profile webui
./scripts/start.sh --stop && ./scripts/start.sh --daemon
```

## Uninstall

```bash
./install.sh --uninstall            # installed skills
rm -rf frontend/node_modules frontend/dist
```

Python packages and your pipelines under `backend/data/` are left alone.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| "UI index file not found" in logs | Frontend not built | `cd frontend && npm install && npm run build` |
| Blank page at `:8000` | Stale or partial build | Delete `frontend/dist`, rebuild |
| `DataFlow core is incomplete` | A prior initialization failed partway through | Move the incomplete `backend/data/dataflow_core/` aside, then re-run the install |
| `<cli>: command not found` in backend logs | Agent CLI not on the backend's PATH | Set `DATAFLOW_CLAUDE_CLI` / `DATAFLOW_CODEX_CLI` to an absolute path before starting |
| Chat replies empty, immediate `done` | Agent auth failed | Confirm the key is exported in the shell that started the backend; for Codex try `codex login` |
| Agent invents operators | Skill not loaded | Re-run `./install.sh --profile webui --force` |
| `lang="zh"` yields 0 rows on English data | Stale skill | Same as above — the skill encodes the language-detection policy |
| Cursor sees no MCP tools | Not enabled in IDE, or backend down | Enable in Settings; check `./scripts/start.sh --status` |
| Pipeline nodes stack on one another | Old layout code | Fixed on `main`; ensure you are current |

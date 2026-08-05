# Profile: `harness`

The DataFlow Harness backend: FastAPI service, MCP server, operator registry, pipeline validation. No frontend, no Node.js.

```bash
./install.sh --profile harness
```

## What this is for

You drive DataFlow from Claude Code, Codex or Cursor and want the agent to query your **actual** operator registry, validate a pipeline before committing it, and execute it — without a browser.

This is a real product layer, not "webui with the frontend deleted". It installs on a machine with no Node.js.

## What this is not for

- A visual DAG you can drag around → use [`webui`](webui.md)
- Avoiding a running server entirely → use [`skills`](skills.md)

## Prerequisites

- Python 3.10+ (3.10 recommended) in an activated venv or conda environment
- uv (the default Python package installer; use `--pip` as a fallback)
- No Node.js required, and none is installed

If your shell's `python3` is older (macOS commonly still provides 3.9), choose
the intended interpreter explicitly. The installer installs and runs everything
through that same interpreter:

```bash
DATAFLOW_PYTHON="$(command -v python3.10)" ./install.sh --profile harness
```

## Install

```bash
./install.sh --profile harness --check      # verify prerequisites only
./install.sh --profile harness --dry-run    # print the plan, change nothing
./install.sh --profile harness
# If uv is unavailable or disallowed:
./install.sh --profile harness --pip
```

Steps: install `open-dataflow` with uv → install `backend/requirements.txt` → initialize the DataFlow core data directory → render and install the harness + standalone skills. Pass `--pip` to use pip explicitly.

Afterwards the installer verifies its own boundaries: it fingerprints every path
listed in this profile's `must_not_touch` (`frontend/src`, `frontend/package.json`,
`node_modules`, `.mcp.json`, `~/.codex/config.toml`, `~/.cursor/mcp.json`) before
and after the install, comparing every file's content hash, and fails if anything
changed.

## Run

```bash
./scripts/start.sh              # foreground
./scripts/start.sh --daemon     # background; PID in .backend.pid
./scripts/start.sh --status
./scripts/start.sh --stop
```

Defaults come from `installers/config.sh`: host `0.0.0.0`, port `8000`, MCP at `/mcp`. Override with `DATAFLOW_HOST`, `DATAFLOW_PORT`.

Opening `http://localhost:8000/` in this profile logs a warning about a missing UI index and serves no canvas. That is expected — the API and MCP endpoint are what this profile provides.

### Runtime surface

| | |
|---|---|
| API | `http://localhost:8000/api/v1/...` |
| MCP | `http://localhost:8000/mcp` (SSE transport) |
| Docs | `http://localhost:8000/docs` |
| Runtime data | `backend/data/` (registries, `ops.json`, preferences) |
| Cache | `backend/cache_local/` (pipeline execution scratch) |

There is **no authentication**. This is a single-user, local-first tool: binding to `0.0.0.0` exposes the API to your whole network, so keep it on a trusted network or set `DATAFLOW_HOST=127.0.0.1`.

## Connect an agent

Separate, explicit step — installing wrote no agent config:

```bash
./install.sh configure-agent --agent claude               # writes .mcp.json in this repo
./install.sh configure-agent --agent codex  --scope user  # asks before writing ~/.codex/
./install.sh configure-agent --agent cursor              # writes .cursor/mcp.json
./install.sh configure-agent --agent cursor --dry-run    # show the file, write nothing
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

## Minimal verification

With the backend running:

```bash
curl -sf http://localhost:8000/api/v1/operators/categories | head -c 200
```

End to end through an agent:

```bash
claude --print --mcp-config .mcp.json --output-format text \
  "call mcp__dataflow__list_operator_categories and report the result"
```

Expect categories such as `core_text`, `general_text`, `reasoning`.

## Upgrade

```bash
git pull
./install.sh --profile harness          # idempotent; skips satisfied steps
./scripts/start.sh --stop && ./scripts/start.sh --daemon
```

## Uninstall

```bash
./install.sh --uninstall     # removes installed skills
```

Python packages are left in place; remove them with pip yourself. Runtime data under `backend/data/` is never deleted automatically — it holds your pipelines.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot import app.main` | Backend deps missing | Re-run the install; check you're in the right Python env |
| `DataFlow core is incomplete` | A previous initialization failed partway through | Move the incomplete `backend/data/dataflow_core/` aside, then re-run the install; the installer will not merge into an unknown partial directory |
| Agent reports "MCP server not reachable" | Backend not running, or wrong port | `./scripts/start.sh --status`; re-run `configure-agent` if you changed the port |
| Cursor rejects MCP responses | Old build wrapping JSON-RPC in the API envelope | Fixed on `main`; make sure you are current |
| Tool calls fail with "tool not found" | Whitelist and routes disagree | `python3 installers/checks/check_mcp_whitelist.py` |
| Codex shows no MCP tools | Config read only at startup | Restart the Codex session |
| `Failed to process parameter: llm_serving` | Serving not assigned to every LLM operator | Assign a serving to each LLM operator, not just the first |

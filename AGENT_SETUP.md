# AGENT_SETUP.md

> **You are an AI agent.** This document tells you how to set up
> DataFlow-WebUI from scratch and make yourself work with it. A human can
> also read it, but the prose is written for you.

The user has asked you to configure DataFlow-WebUI. Your goal: get the
system to a state where the user can open `http://localhost:8000/` and
build data pipelines through natural language — either via the WebUI chat
panel or directly through you in their IDE/terminal.

---

## TL;DR — The Fast Path

```bash
# 1. Install everything (Python deps, Node build, DataFlow, MCP configs)
./scripts/setup_all.sh

# 2. Start the backend
./scripts/start.sh --daemon

# 3. Verify MCP works
curl -sf http://localhost:8000/mcp | head -c 100 && echo " ← MCP OK"
```

If all three succeed, you're done. Skip to **Section 7** for behavioral rules.

If anything fails, read on for the detailed flow.

---

## Usage Modes

### Mode A: WebUI Dispatch (Claude Code, Codex)

The WebUI backend spawns your CLI headlessly when the user chats in the
browser. You receive a system prompt, MCP config, and a user message.

**Agents in this mode:** Claude Code (`claude`), Codex (`codex`).

### Mode B: IDE / Terminal (Cursor IDE, Claude Code terminal)

You run in the user's own IDE or terminal. You connect to the same MCP
server and can push pipelines to the WebUI canvas.

**Agents in this mode:** Cursor (in Cursor IDE), Claude Code (when run
directly in this repo).

---

## 1. Identify yourself

- If you read `CLAUDE.md` first → you are **Claude Code**.
- If you read `AGENTS.md` first → you are **Codex**.
- If you read `.cursor/rules/*.mdc` → you are **Cursor** (IDE mode).

If unsure, ask the user.

---

## 2. Full environment setup

You are authorised to run the one-command installer:

```bash
./scripts/setup_all.sh
```

This script (idempotent, safe to re-run) will:
1. Check Python 3.10+ and Node.js 20+ are available
2. Install the DataFlow framework (`pip install open-dataflow`)
3. Install backend Python dependencies (`pip install -r backend/requirements.txt`)
4. Install frontend Node packages and build (`npm install && npm run build`)
5. Initialize DataFlow core data directory
6. Configure MCP for all agents (delegates to `./scripts/setup_agent.sh all`)

**If prerequisites are missing** (Python or Node not installed), the script
will report what's needed. Tell the user exactly what to install:
- Python: `https://python.org` or their system package manager
- Node.js: `nvm install 20` (recommend [nvm](https://github.com/nvm-sh/nvm))

---

## 3. Start the backend

```bash
./scripts/start.sh           # foreground (Ctrl+C to stop)
./scripts/start.sh --daemon  # background mode
./scripts/start.sh --status  # check if running
./scripts/start.sh --stop    # stop background server
```

The backend serves both the WebUI frontend and the MCP server at
`http://localhost:8000/mcp`.

If the backend is already running, `start.sh` will detect it and skip.

---

## 4. Configure MCP for your agent

`setup_all.sh` already ran `setup_agent.sh all`, but if you need to
reconfigure just your own agent:

```bash
./scripts/setup_agent.sh claude   # or cursor / codex / all
```

### What gets written per agent

| Agent | Files written |
|---|---|
| Claude Code | `.mcp.json` (repo root) |
| Cursor IDE | `.cursor/mcp.json` + `.cursor/rules/dataflow-pipeline.mdc` |
| Codex | `~/.codex/config.toml` (appends `[mcp_servers.dataflow]`) + `AGENTS.md` |

---

## 5. Activate MCP in your IDE/CLI

Having the config file on disk is necessary but not always sufficient.

### Cursor IDE

`.cursor/mcp.json` defines the server, but Cursor requires the user to
**enable** it in IDE settings. If you cannot see `dataflow` MCP tools,
guide the user:

1. Open **Cursor Settings** (Cmd/Ctrl + Shift + J → Settings)
2. Navigate to **Features → MCP Servers** (or search "MCP")
3. Find `dataflow` (from `.cursor/mcp.json`). Toggle it **ON**.
4. If it shows "failed", ensure backend is running: `./scripts/start.sh --status`
5. Click "Refresh" or restart Cursor to reconnect.

### Codex

Codex reads `~/.codex/config.toml` at startup. If MCP tools are missing:

1. Verify `[mcp_servers.dataflow]` exists with `enabled = true`
2. Verify backend is running
3. Restart the codex session (config is read at startup only)

If the block is missing, write it:
```bash
cat >> ~/.codex/config.toml << 'EOF'

[mcp_servers.dataflow]
url = "http://localhost:8000/mcp"
enabled = true
tool_timeout_sec = 120
EOF
```

### Claude Code

When spawned by the WebUI backend, Claude receives `--mcp-config .mcp.json`
automatically. When running in terminal, ensure `.mcp.json` exists at repo
root (run `./scripts/setup_agent.sh claude` if missing).

---

## 6. Verify end-to-end

| Agent kind | Verify command |
|---|---|
| Claude Code | `claude --print --mcp-config .mcp.json --output-format text "call mcp__dataflow__list_operator_categories and report the result"` |
| Codex | `codex exec --json --sandbox workspace-write "call the dataflow MCP tool list_operator_categories and report the result"` |
| Cursor IDE | In Agent panel: "call the dataflow MCP tool list_operator_categories and report the result" |

Expected: a list of categories like `core_text`, `general_text`, `reasoning`, …

If it fails:
1. **Backend not running** → `./scripts/start.sh`
2. **MCP not activated** → See section 5
3. **Auth missing** → See section below

### Authentication

| Agent | Auth |
|---|---|
| **Claude Code** | `ANTHROPIC_API_KEY` (or `ANTHROPIC_BASE_URL` for gateway) |
| **Codex (API key)** | `OPENAI_API_KEY` + optional `OPENAI_BASE_URL` |
| **Codex (OAuth)** | No key needed — run `codex login` (ChatGPT Plus/Pro) |
| **Cursor IDE** | Built-in auth, no env var needed |

If auth fails, tell the user which env var to export or suggest `codex login`.
Do NOT prompt for key values in chat or write them to disk.

---

## 7. Behavioral rules (canonical skill)

Once setup is complete, follow the construction skill at
`.claude/skills/generating-dataflow-pipeline/SKILL.md`. Key rules:

- **Operator info via MCP only.** Use `list_operator_categories` →
  `list_operators(category=…)` → `get_operator_detail_by_name`.
  Do NOT browse source directories.
- **Language detection before setting `lang`.** Call `get_dataset_preview`
  on the dataset before deciding `lang="zh"` vs `lang="en"`.
- **Validate before create.** Call `validate_pipeline_config` before
  `create_pipeline` / `update_pipeline`.
- **Never auto-execute.** Don't call `execute_pipeline` unless the user
  explicitly asks.
- **One pipeline per turn.** Use `update_pipeline` to refine.

---

## 8. Authorization scope

You ARE authorised to:

- Run `./scripts/setup_all.sh` and `./scripts/start.sh`
- Run `pip install` and `npm install` for **this project's dependencies only**
- Edit `.mcp.json`, `.cursor/mcp.json`, `.cursor/rules/*.mdc`, `AGENTS.md`
  inside this repo
- Edit `~/.codex/config.toml` in the user's home directory
- Run `./scripts/setup_agent.sh <kind>`

You are NOT authorised to:

- Edit any other file in `~` (no `.bashrc`, `.zshrc`, ssh config, etc.)
- Read or write API keys outside standard env-var locations
- Install system packages (apt, brew, etc.) without explicit user permission
- Install agent CLIs without explicit user permission
- Touch shared infrastructure (other repos, databases, cloud resources)

---

## 9. If something is off-script, tell the user

Examples of "stop and ask":

- Prerequisites missing (Python < 3.10, no Node.js) — tell them what to install
- API key gateway is unusual (Azure OpenAI, custom endpoints)
- A previous agent left MCP config pointing at a different port
- The user wants you to install a CLI or system package
- Codex OAuth login has expired — suggest `codex login` again

Self-modifying the user's environment without telling them is a worse
failure mode than pausing for one round trip.

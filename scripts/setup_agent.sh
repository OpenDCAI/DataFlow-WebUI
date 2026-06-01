#!/usr/bin/env bash
# setup_agent.sh — configure Claude Code, Cursor, or Codex to drive
# DataFlow-WebUI through its in-process MCP server.
#
# Usage:
#   ./scripts/setup_agent.sh claude
#   ./scripts/setup_agent.sh cursor
#   ./scripts/setup_agent.sh codex
#   ./scripts/setup_agent.sh all          # tries each in turn, warns on missing CLIs
#   ./scripts/setup_agent.sh --print-config <agent>   # print what would be written, don't write
#
# What it does (per agent):
#   claude / codex:
#     - Checks the agent's CLI binary is on PATH; prints install hint and skips if not.
#     - Checks the relevant API-key env var; for codex, missing key is OK (OAuth fallback).
#     - Writes the agent's MCP config in the location that agent reads natively.
#     - Writes / refreshes the agent-specific instruction file from the canonical
#       skill content under .claude/skills/.
#     - Prints a verification command.
#   cursor:
#     - Writes .cursor/mcp.json so Cursor IDE can discover the DataFlow MCP server.
#     - Writes .cursor/rules/dataflow-pipeline.mdc from the canonical skill.
#     - Does NOT check for cursor-agent CLI (Cursor is IDE-mode only).
#
# Idempotent: re-running leaves the system in the same state.

set -euo pipefail

# Resolve repo root (parent of this script's parent)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBUI_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WEBUI_ROOT"

# ---------- color helpers ---------------------------------------------------
if [[ -t 1 ]]; then
  C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_RED=$'\033[31m'
  C_BLUE=$'\033[34m'; C_BOLD=$'\033[1m'; C_RESET=$'\033[0m'
else
  C_GREEN=""; C_YELLOW=""; C_RED=""; C_BLUE=""; C_BOLD=""; C_RESET=""
fi

info()  { printf '%s[setup-agent]%s %s\n'              "$C_BLUE"   "$C_RESET" "$*"; }
ok()    { printf '%s[setup-agent]%s %sOK%s     %s\n'   "$C_BLUE"   "$C_RESET" "$C_GREEN" "$C_RESET" "$*"; }
warn()  { printf '%s[setup-agent]%s %sWARN%s   %s\n'   "$C_BLUE"   "$C_RESET" "$C_YELLOW" "$C_RESET" "$*" 1>&2; }
err()   { printf '%s[setup-agent]%s %sERROR%s  %s\n'   "$C_BLUE"   "$C_RESET" "$C_RED"    "$C_RESET" "$*" 1>&2; }
header(){ printf '\n%s── %s ──%s\n' "$C_BOLD" "$*" "$C_RESET"; }

DRY_RUN=0
if [[ "${1:-}" == "--print-config" ]]; then
  DRY_RUN=1
  shift
fi

agent="${1:-}"

usage() {
  cat <<EOF
Usage: $0 <agent>
       $0 --print-config <agent>

  agent ::= claude | cursor | codex | all

EOF
  exit 1
}

[[ -n "$agent" ]] || usage

# ---------- shared helpers --------------------------------------------------
MCP_URL="http://localhost:8000/mcp"
CANONICAL_SKILL_DIR="$WEBUI_ROOT/.claude/skills/generating-dataflow-pipeline"
CANONICAL_SKILL_FILE="$CANONICAL_SKILL_DIR/SKILL.md"

write_or_print() {
  # Usage: write_or_print <dest_path> <content_string_var>
  local dest="$1" content_var="$2"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '%s── would write: %s ──%s\n' "$C_BOLD" "$dest" "$C_RESET"
    printf '%s\n' "${!content_var}"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  printf '%s\n' "${!content_var}" > "$dest"
  ok "wrote $dest"
}

require_cli() {
  # Usage: require_cli <env-override-var> <default-cmd> <install-hint>
  local env_var="$1" default_cmd="$2" hint="$3"
  local resolved="${!env_var:-}"
  resolved="${resolved:-$default_cmd}"
  if ! command -v "$resolved" >/dev/null 2>&1; then
    warn "$resolved not found on PATH. $hint"
    return 1
  fi
  ok "found CLI: $resolved"
  return 0
}

check_api_key() {
  # Usage: check_api_key <var> <doc>
  local var="$1" doc="$2"
  local val="${!var:-}"
  if [[ -z "$val" ]]; then
    warn "$var is not set; the agent will fail to authenticate. $doc"
  else
    ok "$var is set (${#val} chars)"
  fi
}

# ---------- per-agent setup -------------------------------------------------

setup_claude() {
  header "Claude Code"
  local cli_ok=1
  require_cli DATAFLOW_CLAUDE_CLI claude \
    "Install with: curl -fsSL https://claude.ai/code/install.sh | sh" || cli_ok=0
  if [[ "$cli_ok" -eq 1 ]]; then
    check_api_key ANTHROPIC_API_KEY "Get one at https://console.anthropic.com (or set ANTHROPIC_BASE_URL for a gateway)."
  fi

  # Claude reads .mcp.json at the cwd where it was launched. The WebUI backend
  # already passes --mcp-config $WEBUI_ROOT/.mcp.json explicitly; we just keep
  # the file in sync so a developer running `claude` directly in the repo
  # gets the same MCP server.
  local mcp_path="$WEBUI_ROOT/.mcp.json"
  local mcp_content
  mcp_content=$(cat <<JSON
{
  "mcpServers": {
    "dataflow": {
      "type": "sse",
      "url": "$MCP_URL"
    }
  }
}
JSON
  )
  write_or_print "$mcp_path" mcp_content

  if [[ "$cli_ok" -eq 1 ]]; then
    ok "Claude Code is configured. Verify with:"
    info "    claude --print --mcp-config .mcp.json --output-format text \\"
    info "      \"call mcp__dataflow__list_operator_categories and report the result\""
  else
    warn "Claude config files written but CLI is missing — install before starting backend."
  fi
}

setup_cursor() {
  header "Cursor (IDE 模式)"
  info "配置 Cursor IDE 使其能透过 MCP 把 pipeline 推到本 WebUI。"
  info "注意: Cursor 不通过 WebUI 前端调度，而是在 IDE 内直接使用 Agent。"

  # Project-scoped MCP config — Cursor auto-reads .cursor/mcp.json
  local proj_mcp="$WEBUI_ROOT/.cursor/mcp.json"
  local proj_content
  proj_content=$(cat <<JSON
{
  "mcpServers": {
    "dataflow": {
      "type": "sse",
      "url": "$MCP_URL"
    }
  }
}
JSON
  )
  write_or_print "$proj_mcp" proj_content

  # User-scoped fallback so Cursor IDE opened from outside this repo
  # also sees the dataflow server.
  local user_mcp="$HOME/.cursor/mcp.json"
  if [[ -f "$user_mcp" ]] && grep -q '"dataflow"' "$user_mcp"; then
    ok "$user_mcp already lists a 'dataflow' server; not overwriting"
  else
    write_or_print "$user_mcp" proj_content
  fi

  # Cursor instruction rules (regenerated from canonical skill)
  if [[ -f "$CANONICAL_SKILL_FILE" ]]; then
    local rule_path="$WEBUI_ROOT/.cursor/rules/dataflow-pipeline.mdc"
    local skill_body
    skill_body=$(<"$CANONICAL_SKILL_FILE")
    local rule_content
    rule_content=$(cat <<MDC
---
description: DataFlow pipeline construction skill (auto-generated from .claude/skills/generating-dataflow-pipeline/SKILL.md by scripts/setup_agent.sh).
globs: ["**/*.py", "**/*.jsonl", "**/*.json"]
alwaysApply: true
---

# DataFlow pipeline construction (Cursor)

This rule mirrors the canonical Claude skill so Cursor produces the same
pipelines as Claude Code in this repo. Do NOT edit by hand — re-run
\`./scripts/setup_agent.sh cursor\` after changing the skill.

$skill_body
MDC
    )
    write_or_print "$rule_path" rule_content
  else
    warn "canonical skill not found at $CANONICAL_SKILL_FILE; skipping .cursor/rules generation"
  fi

  ok "Cursor IDE 配置完成。使用方式:"
  info "  1. 用 Cursor 打开本项目目录"
  info "  2. 确保 WebUI 后端已启动 (uvicorn app.main:app)"
  info "  3. 在 Cursor Agent 中直接对话，MCP 工具会自动可用"
  info "  4. Agent 可通过 MCP 创建/执行 pipeline，结果会同步到 WebUI 画布"
}

setup_codex() {
  header "Codex"
  local cli_ok=1
  require_cli DATAFLOW_CODEX_CLI codex \
    "Install per https://openai-codex.mintlify.app — typically: npm i -g @openai/codex" || cli_ok=0

  # Codex supports two auth modes:
  #   1. OPENAI_API_KEY (or OPENAI_BASE_URL for 中转/gateway)
  #   2. `codex login` OAuth — uses ChatGPT Plus subscription, no API key needed
  if [[ "$cli_ok" -eq 1 ]]; then
    local api_key="${OPENAI_API_KEY:-}"
    if [[ -n "$api_key" ]]; then
      ok "OPENAI_API_KEY is set (${#api_key} chars)"
      if [[ -n "${OPENAI_BASE_URL:-}" ]]; then
        ok "OPENAI_BASE_URL is set (中转/gateway mode): $OPENAI_BASE_URL"
      fi
    else
      info "OPENAI_API_KEY 未设置 — codex 会 fallback 到 \`codex login\` 的 OAuth 凭证（ChatGPT Plus）。"
      info "如需使用 API key 模式: export OPENAI_API_KEY=sk-..."
      info "如需使用中转: export OPENAI_API_KEY=... && export OPENAI_BASE_URL=https://your-gateway/v1"
      info "如需使用 ChatGPT Plus 登录: codex login"
    fi
  fi

  # Codex reads ~/.codex/config.toml. Append [mcp_servers.dataflow] block
  # idempotently — keep any other servers the user already has.
  local codex_dir="$HOME/.codex"
  local codex_cfg="$codex_dir/config.toml"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    info "would create $codex_dir if missing"
  else
    mkdir -p "$codex_dir"
  fi
  if [[ ! -f "$codex_cfg" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      info "would create $codex_cfg"
    else
      : > "$codex_cfg"
      ok "created $codex_cfg"
    fi
  fi

  if [[ -f "$codex_cfg" ]] && grep -q '^\[mcp_servers\.dataflow\]' "$codex_cfg" 2>/dev/null; then
    ok "$codex_cfg already has [mcp_servers.dataflow]; leaving it intact"
  else
    local block
    block=$(cat <<TOML

[mcp_servers.dataflow]
url = "$MCP_URL"
enabled = true
tool_timeout_sec = 120
TOML
    )
    if [[ "$DRY_RUN" -eq 1 ]]; then
      printf '%s── would append to: %s ──%s\n' "$C_BOLD" "$codex_cfg" "$C_RESET"
      printf '%s\n' "$block"
    else
      printf '%s\n' "$block" >> "$codex_cfg"
      ok "appended [mcp_servers.dataflow] to $codex_cfg"
    fi
  fi

  # Codex reads AGENTS.md at the cwd. Generate one from the canonical skill.
  if [[ -f "$CANONICAL_SKILL_FILE" ]]; then
    local agents_md="$WEBUI_ROOT/AGENTS.md"
    local skill_body
    skill_body=$(<"$CANONICAL_SKILL_FILE")
    local agents_content
    agents_content=$(cat <<MD
# Agent Instructions (DataFlow-WebUI)

> Auto-generated from \`.claude/skills/generating-dataflow-pipeline/SKILL.md\`
> by \`./scripts/setup_agent.sh codex\`. Do NOT edit by hand — re-run the
> script after changing the canonical skill.

This file is read by **Codex** (the OpenAI \`codex\` CLI) and any other agent
that follows the AGENTS.md convention. Claude Code reads
\`.claude/skills/\` directly; Cursor reads \`.cursor/rules/\` directly. All
three sources must stay in sync — run \`./scripts/setup_agent.sh all\` to
regenerate.

For first-time setup of any agent, read \`AGENT_SETUP.md\` first.

---

$skill_body
MD
    )
    write_or_print "$agents_md" agents_content
  else
    warn "canonical skill not found at $CANONICAL_SKILL_FILE; skipping AGENTS.md generation"
  fi

  if [[ "$cli_ok" -eq 1 ]]; then
    ok "Codex is configured. Verify with:"
    info "    codex exec --json --full-auto \\"
    info "      \"call the dataflow MCP tool list_operator_categories and report the result\" | head"
  else
    warn "Codex config files written but codex is missing — install before starting backend."
  fi
}

# ---------- dispatcher ------------------------------------------------------

case "$agent" in
  claude) setup_claude ;;
  cursor) setup_cursor ;;
  codex)  setup_codex ;;
  all)
    setup_claude || true
    setup_cursor || true
    setup_codex || true
    ;;
  -h|--help) usage ;;
  *)
    err "unknown agent: $agent"
    usage
    ;;
esac

header "Done"
info "WebUI 后端通过以下环境变量定位 agent CLI:"
info "  DATAFLOW_CLAUDE_CLI=\${DATAFLOW_CLAUDE_CLI:-claude}"
info "  DATAFLOW_CODEX_CLI=\${DATAFLOW_CODEX_CLI:-codex}"
info ""
info "Cursor 为 IDE 模式，不由后端调度 — 在 Cursor IDE 中打开本项目即可使用。"
info "Backend reads agent default from DATAFLOW_DEFAULT_AGENT (defaults to claude)."
info "Pick the agent for a chat session in the WebUI dropdown next to the chat title."

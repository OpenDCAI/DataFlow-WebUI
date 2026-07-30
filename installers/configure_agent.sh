#!/usr/bin/env bash
# configure_agent.sh — point a coding agent at this repo's MCP server.
#
#   ./install.sh configure-agent --agent claude
#   ./install.sh configure-agent --agent codex  --scope user
#   ./install.sh configure-agent --agent cursor --scope project --dry-run
#
# Deliberately separate from installing (plan item P1-04). Two rules:
#
#   1. Default scope is PROJECT. Files in your home directory are only touched
#      with --scope user, and even then the diff is shown first.
#   2. Existing config is merged, never clobbered. An unrelated MCP server you
#      already configured survives.
#
# No API keys are read, written or logged. Agents pick those up from the
# environment at run time.

set -euo pipefail

DF_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DF_REPO_ROOT"

# shellcheck source=config.sh
source "$DF_REPO_ROOT/installers/config.sh"
# Read by the logging helpers in lib/common.sh, sourced on the next line.
# shellcheck disable=SC2034
DF_TAG="configure"
# shellcheck source=lib/common.sh
source "$DF_REPO_ROOT/installers/lib/common.sh"

usage() {
  cat <<'EOF'
Configure a coding agent to use this repo's DataFlow MCP server.

Usage:
  ./install.sh configure-agent --agent <claude|codex|cursor> [options]

Options:
  --agent <name>   claude | codex | cursor   (required)
  --scope <s>      project (default) | user
                   project → writes inside this repo only
                   user    → writes into your home directory, after showing a diff
  --dry-run        Print the exact file contents that would be written; write nothing
  --yes            Skip the confirmation prompt for --scope user
  --force          Redirect an existing 'dataflow' MCP entry that points at a
                   different URL. Without this, such a conflict is refused.
  --verbose        Show extra detail
  -h, --help       This message

What gets written:

  claude  project: .mcp.json
          user:    ~/.claude.json is NOT touched — Claude reads .mcp.json from
                   the directory it starts in, so project scope is sufficient.
  codex   user ONLY: ~/.codex/config.toml — [mcp_servers.dataflow] merged in.
          Codex reads no other location and has no flag to redirect it, so
          --scope project is rejected rather than writing an ignored file.
  cursor  project: .cursor/mcp.json
          user:    ~/.cursor/mcp.json  — merged, existing servers preserved

Nothing here installs an agent CLI or handles credentials.
EOF
}

AGENT=""
SCOPE="project"
DRY_RUN=0
ASSUME_YES=0
FORCE=0

# SC2034: DF_VERBOSE is read by debug() in lib/common.sh, which is sourced
# above; the linter cannot see across that boundary.
# shellcheck disable=SC2034
while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)   AGENT="${2:-}"; shift 2 ;;
    --agent=*) AGENT="${1#*=}"; shift ;;
    --scope)   SCOPE="${2:-}"; shift 2 ;;
    --scope=*) SCOPE="${1#*=}"; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --yes|-y)  ASSUME_YES=1; shift ;;
    --force|-f) FORCE=1; shift ;;
    --verbose|-v) DF_VERBOSE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) err "unknown option: $1"; echo; usage >&2; exit 2 ;;
  esac
done

[[ -n "$AGENT" ]] || { err "--agent is required (claude|codex|cursor)"; echo; usage >&2; exit 2; }
case "$AGENT" in claude|codex|cursor) ;; *) err "unknown agent: $AGENT"; exit 2 ;; esac
case "$SCOPE" in project|user) ;; *) err "invalid --scope: $SCOPE (project|user)"; exit 2 ;; esac

# ---------- diff + confirm + write -----------------------------------------
show_diff() {
  # show_diff <path> <new-content>
  local path="$1" new="$2"
  if [[ -f "$path" ]]; then
    printf '\n%s── diff for %s ──%s\n' "$C_BOLD" "$path" "$C_RESET"
    if diff -u "$path" <(printf '%s\n' "$new") > /tmp/df_cfg_diff.$$ 2>&1; then
      printf '  (no change — file already matches)\n'
      rm -f /tmp/df_cfg_diff.$$
      return 1
    fi
    sed 's/^/  /' /tmp/df_cfg_diff.$$
    rm -f /tmp/df_cfg_diff.$$
  else
    printf '\n%s── new file %s ──%s\n' "$C_BOLD" "$path" "$C_RESET"
    printf '%s\n' "$new" | sed 's/^/  + /'
  fi
  return 0
}

confirm_or_exit() {
  local path="$1"
  if [[ "$ASSUME_YES" -eq 1 ]]; then
    debug "--yes given, not prompting"
    return 0
  fi
  printf '\n%sWrite this to %s? [y/N] %s' "$C_YELLOW" "$path" "$C_RESET"
  local reply=""
  read -r reply < /dev/tty || reply=""
  case "$reply" in
    y|Y|yes|YES) return 0 ;;
    *) info "skipped $path (not confirmed)"; return 1 ;;
  esac
}

write_config() {
  # write_config <path> <content> <needs-confirm:0|1>
  local path="$1" content="$2" needs_confirm="$3"

  if ! show_diff "$path" "$content"; then
    return 0   # already identical
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    plan "would write $path"
    return 0
  fi

  if [[ "$needs_confirm" -eq 1 ]]; then
    confirm_or_exit "$path" || return 0
  fi

  mkdir -p "$(dirname "$path")"
  printf '%s\n' "$content" > "$path"
  ok "wrote $path"
}

NEEDS_CONFIRM=0
[[ "$SCOPE" == "user" ]] && NEEDS_CONFIRM=1

# (A literal MCP_JSON block used to live here. It was replaced by the merge
#  helpers below, which read the existing file first, and lingered unused —
#  removed so there is only one definition of what gets written.)

# ---------- merge helpers ---------------------------------------------------
merge_mcp_json() {
  # Merge a "dataflow" entry into an existing mcpServers object, preserving
  # every other server the user configured — and every other key inside the
  # dataflow entry itself.
  local path="$1" rc=0 out=""
  local force_flag=""
  [[ "$FORCE" -eq 1 ]] && force_flag="--force"
  out=$("$DF_PYTHON" "$DF_REPO_ROOT/installers/lib/mcp_json_config.py" \
          "$path" "$DF_MCP_URL" $force_flag 2>/tmp/df_json_err.$$) || rc=$?
  if [[ "$rc" -eq 0 ]]; then
    printf '%s' "$out"
    rm -f /tmp/df_json_err.$$
    return 0
  fi
  case "$rc" in
    3) err "$path exists but is not valid JSON — refusing to modify it."
       err "Fix or move the file, then re-run. Nothing was written." ;;
    4) err "$(cat /tmp/df_json_err.$$)"
       err "Refusing to redirect an MCP server you configured deliberately."
       err "Re-run with --force to point it at $DF_MCP_URL." ;;
    *) err "failed to process $path (exit $rc)"
       [[ -s /tmp/df_json_err.$$ ]] && err "$(cat /tmp/df_json_err.$$)" ;;
  esac
  rm -f /tmp/df_json_err.$$
  return 1
}

merge_codex_toml() {
  # Delegates to installers/lib/codex_config.py, which parses the file as TOML
  # before touching it, preserves keys we do not manage, and refuses to redirect
  # an existing dataflow entry that points somewhere else.
  local path="$1" rc=0 out=""
  local force_arg=""
  [[ "$FORCE" -eq 1 ]] && force_arg="--force"

  out=$("$DF_PYTHON" "$DF_REPO_ROOT/installers/lib/codex_config.py" \
          "$path" "$DF_MCP_URL" $force_arg 2>/tmp/df_codex_err.$$) || rc=$?

  case "$rc" in
    0) printf '%s' "$out" ;;
    2)
      err "cannot validate $path: no TOML parser available."
      err "Codex config is only edited when it can be parsed first. Either:"
      err "  - pip install -r installers/requirements-configure.txt   (adds tomli), or"
      err "  - run this with Python 3.11+ (DATAFLOW_PYTHON=python3.11 ...), or"
      err "  - add the block by hand:"
      err ""
      err "      [mcp_servers.dataflow]"
      err "      url = \"$DF_MCP_URL\""
      err "      enabled = true"
      err "      tool_timeout_sec = 120"
      rm -f /tmp/df_codex_err.$$
      return 1 ;;
    3)
      err "$path exists but is not valid TOML — refusing to modify it."
      err "$(cat /tmp/df_codex_err.$$)"
      err "Fix or move the file, then re-run. Nothing was written."
      rm -f /tmp/df_codex_err.$$
      return 1 ;;
    4)
      err "$(cat /tmp/df_codex_err.$$)"
      err "Refusing to redirect an MCP server you configured deliberately."
      err "Re-run with --force to point it at $DF_MCP_URL."
      rm -f /tmp/df_codex_err.$$
      return 1 ;;
    *)
      err "failed to read $path (exit $rc)"
      [[ -s /tmp/df_codex_err.$$ ]] && err "$(cat /tmp/df_codex_err.$$)"
      rm -f /tmp/df_codex_err.$$
      return 1 ;;
  esac
  rm -f /tmp/df_codex_err.$$
}

# ---------- per-agent ------------------------------------------------------
header "Configure $AGENT (scope: $SCOPE)"
info "MCP endpoint: $DF_MCP_URL"

case "$AGENT" in
  claude)
    if [[ "$SCOPE" == "user" ]]; then
      warn "Claude Code reads .mcp.json from the directory it starts in."
      warn "There is no user-level MCP file to write, so project scope is what you want."
      info "Run without --scope user."
      exit 0
    fi
    target="$DF_REPO_ROOT/.mcp.json"
    content=$(merge_mcp_json "$target") || exit 1
    write_config "$target" "$content" 0
    info ""
    info "Verify (backend must be running):"
    info "  claude --print --mcp-config .mcp.json --output-format text \\"
    info "    \"call mcp__dataflow__list_operator_categories and report the result\""
    ;;

  cursor)
    if [[ "$SCOPE" == "project" ]]; then
      target="$DF_REPO_ROOT/.cursor/mcp.json"
    else
      target="$HOME/.cursor/mcp.json"
    fi
    content=$(merge_mcp_json "$target") || exit 1
    write_config "$target" "$content" "$NEEDS_CONFIRM"
    info ""
    info "Cursor requires you to enable the server once in the IDE:"
    info "  Settings → Features → MCP Servers → toggle 'dataflow' ON"
    ;;

  codex)
    # Codex reads ONLY ~/.codex/config.toml and has no flag to point at an
    # alternate config file — see the note at the top of
    # backend/app/services/agents/codex_adapter.py. A project-scoped file would
    # be written and then silently ignored, so refuse rather than pretend.
    if [[ "$SCOPE" == "project" ]]; then
      warn "Codex has no project-scoped MCP config: it reads only ~/.codex/config.toml,"
      warn "and provides no flag to point it elsewhere. A file inside this repo would"
      warn "be ignored."
      info ""
      info "To configure Codex, write the user-level config explicitly:"
      info "    ./install.sh configure-agent --agent codex --scope user"
      info ""
      info "Preview it first with --dry-run. It merges into any existing config"
      info "and preserves other MCP servers."
      exit 2
    fi
    target="$HOME/.codex/config.toml"
    content=$(merge_codex_toml "$target") || exit 1
    write_config "$target" "$content" "$NEEDS_CONFIRM"
    info ""
    info "Codex reads its config at startup — restart the session to pick this up."
    info "Verify:"
    info "  codex exec --json --full-auto \\"
    info "    \"call the dataflow MCP tool list_operator_categories and report the result\""
    ;;
esac

header "Done"
if [[ "$DRY_RUN" -eq 1 ]]; then
  info "Dry run — nothing was written."
fi
info "Credentials are read from the environment; this script never stores them."

#!/usr/bin/env bash
# setup_agent.sh — DEPRECATED compatibility wrapper.
#
# Replaced by:
#     ./install.sh configure-agent --agent <claude|codex|cursor> [--scope project|user]
#
# Behaviour differences worth knowing:
#   * Default scope is now PROJECT. The old script wrote ~/.codex/config.toml
#     and ~/.cursor/mcp.json without asking; that now needs --scope user and
#     shows a diff first.
#   * Existing MCP servers in your config are merged, not overwritten.
#   * It no longer regenerates AGENTS.md or .cursor/rules — those are generated
#     from skills/canonical/ by installers/generate_agent_assets.py.
#
# See docs/migration/from-setup-scripts.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -t 1 ]]; then
  C_YELLOW=$'\033[33m'; C_BOLD=$'\033[1m'; C_RESET=$'\033[0m'
else
  C_YELLOW=""; C_BOLD=""; C_RESET=""
fi

warn_line() { printf '%s\n' "$*" >&2; }

printf '%s%s[deprecated]%s scripts/setup_agent.sh is superseded by ./install.sh configure-agent\n' \
  "$C_BOLD" "$C_YELLOW" "$C_RESET" >&2

DRY=""
if [[ "${1:-}" == "--print-config" ]]; then
  DRY="--dry-run"
  shift
fi

agent="${1:-}"
if [[ -z "$agent" ]]; then
  warn_line "  Usage: ./install.sh configure-agent --agent <claude|codex|cursor>"
  exit 2
fi

# The old script's "all" fanned out across every agent, and wrote user-level
# config as a side effect. Refuse to guess: writing three config files
# (two in $HOME) is not something to do from a deprecated alias.
if [[ "$agent" == "all" ]]; then
  warn_line "  'all' is no longer supported — it wrote to your home directory implicitly."
  warn_line "  Configure each agent you actually use, e.g.:"
  warn_line "    ./install.sh configure-agent --agent claude"
  warn_line "    ./install.sh configure-agent --agent codex  --scope user"
  warn_line "    ./install.sh configure-agent --agent cursor"
  warn_line "  Details: docs/migration/from-setup-scripts.md"
  exit 2
fi

case "$agent" in
  claude|codex|cursor) ;;
  -h|--help)
    warn_line "  Run: ./install.sh configure-agent --help"
    exit 0 ;;
  *)
    warn_line "  unknown agent: $agent"
    exit 2 ;;
esac

# Codex only reads ~/.codex/config.toml, so it has no project scope; the old
# script always wrote the user-level file. Preserve that behaviour, but the
# new configurator shows a diff and asks before writing.
SCOPE_ARGS=""
if [[ "$agent" == "codex" ]]; then
  SCOPE_ARGS="--scope user"
  warn_line "  Forwarding to: ./install.sh configure-agent --agent codex --scope user ${DRY}"
  warn_line "  Codex has no project-scoped config; this writes \$HOME after showing a diff."
else
  warn_line "  Forwarding to: ./install.sh configure-agent --agent $agent ${DRY}"
  warn_line "  Note: scope defaults to 'project' now. Add --scope user to write \$HOME."
fi
warn_line "  Details: docs/migration/from-setup-scripts.md"
warn_line ""

exec "$REPO_ROOT/install.sh" configure-agent --agent "$agent" ${SCOPE_ARGS} ${DRY:+$DRY}

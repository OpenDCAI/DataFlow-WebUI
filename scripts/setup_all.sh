#!/usr/bin/env bash
# setup_all.sh — DEPRECATED compatibility wrapper.
#
# This script used to install the whole stack AND rewrite agent config in your
# home directory in one pass. That is now two explicit commands:
#
#     ./install.sh --profile webui                    # install
#     ./install.sh configure-agent --agent claude     # opt into agent config
#
# It forwards to the webui profile so existing instructions keep working.
# Scheduled for removal — see docs/migration/from-setup-scripts.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -t 1 ]]; then
  C_YELLOW=$'\033[33m'; C_BOLD=$'\033[1m'; C_RESET=$'\033[0m'
else
  C_YELLOW=""; C_BOLD=""; C_RESET=""
fi

printf '%s%s[deprecated]%s scripts/setup_all.sh is superseded by ./install.sh\n' \
  "$C_BOLD" "$C_YELLOW" "$C_RESET" >&2
printf '  Forwarding to: ./install.sh --profile webui %s\n' "$*" >&2
printf '  Two behaviour changes to know about:\n' >&2
printf '    1. Agent MCP config is NO LONGER written automatically.\n' >&2
printf '       Run: ./install.sh configure-agent --agent <claude|codex|cursor>\n' >&2
printf '    2. Nothing is written to your home directory during install.\n' >&2
printf '  Details: docs/migration/from-setup-scripts.md\n\n' >&2

# --check was the only flag this script accepted; it maps 1:1 onto the new one.
exec "$REPO_ROOT/install.sh" --profile webui "$@"

#!/usr/bin/env bash
# setup_all.sh — One-command full-stack setup for DataFlow-WebUI.
#
# Usage:
#   ./scripts/setup_all.sh           # install everything
#   ./scripts/setup_all.sh --check   # only check, don't install
#
# This script is designed to be run by an AI agent OR a human. It:
#   1. Checks system prerequisites (Python 3.10+, Node.js 20+, pip, npm)
#   2. Installs the DataFlow framework (pip install open-dataflow)
#   3. Installs backend Python dependencies
#   4. Installs frontend Node dependencies and builds
#   5. Initializes DataFlow core data directory
#   6. Configures all agent MCP connections (delegates to setup_agent.sh)
#   7. Prints next steps (how to start the backend)
#
# Idempotent: re-running is safe and skips already-completed steps.

set -euo pipefail

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

info()  { printf '%s[setup]%s %s\n'            "$C_BLUE"   "$C_RESET" "$*"; }
ok()    { printf '%s[setup]%s %sOK%s     %s\n' "$C_BLUE"   "$C_RESET" "$C_GREEN" "$C_RESET" "$*"; }
skip()  { printf '%s[setup]%s %sSKIP%s   %s\n' "$C_BLUE"   "$C_RESET" "$C_GREEN" "$C_RESET" "$*"; }
warn()  { printf '%s[setup]%s %sWARN%s   %s\n' "$C_BLUE"   "$C_RESET" "$C_YELLOW" "$C_RESET" "$*" >&2; }
err()   { printf '%s[setup]%s %sERROR%s  %s\n' "$C_BLUE"   "$C_RESET" "$C_RED"    "$C_RESET" "$*" >&2; }
header(){ printf '\n%s── %s ──%s\n' "$C_BOLD" "$*" "$C_RESET"; }

CHECK_ONLY=0
if [[ "${1:-}" == "--check" || "${1:-}" == "--check-only" ]]; then
  CHECK_ONLY=1
  info "Check-only mode: will report status without installing."
fi

ERRORS=0

# ---------- 1. System prerequisites ----------------------------------------
header "1/7 System Prerequisites"

# PLACEHOLDER_PREREQS

# Python 3.10+
check_python() {
  local py=""
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      py="$candidate"
      break
    fi
  done
  if [[ -z "$py" ]]; then
    err "Python not found. Install Python 3.10+ from https://python.org"
    ERRORS=$((ERRORS + 1))
    return
  fi
  local ver
  ver=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  local major minor
  major="${ver%%.*}"
  minor="${ver#*.}"
  if [[ "$major" -lt 3 ]] || { [[ "$major" -eq 3 ]] && [[ "$minor" -lt 10 ]]; }; then
    err "Python $ver found, but 3.10+ is required."
    ERRORS=$((ERRORS + 1))
  else
    ok "Python $ver ($py)"
  fi
  PYTHON="$py"
}

# Node.js 20+
check_node() {
  if ! command -v node >/dev/null 2>&1; then
    err "Node.js not found. Install Node.js 20+ (recommend: nvm install 20)"
    ERRORS=$((ERRORS + 1))
    return
  fi
  local ver
  ver=$(node -v | sed 's/^v//')
  local major="${ver%%.*}"
  if [[ "$major" -lt 20 ]]; then
    err "Node.js $ver found, but 20+ is required. Run: nvm install 20 && nvm use 20"
    ERRORS=$((ERRORS + 1))
  else
    ok "Node.js $ver"
  fi
}

# pip
check_pip() {
  if ! "$PYTHON" -m pip --version >/dev/null 2>&1; then
    err "pip not available for $PYTHON. Install with: $PYTHON -m ensurepip"
    ERRORS=$((ERRORS + 1))
  else
    ok "pip ($($PYTHON -m pip --version | awk '{print $2}'))"
  fi
}

# npm
check_npm() {
  if ! command -v npm >/dev/null 2>&1; then
    err "npm not found. It should come with Node.js."
    ERRORS=$((ERRORS + 1))
  else
    ok "npm $(npm -v)"
  fi
}

PYTHON="python3"
check_python
check_node
check_pip
check_npm

if [[ "$CHECK_ONLY" -eq 1 ]] && [[ "$ERRORS" -gt 0 ]]; then
  err "$ERRORS prerequisite(s) missing. Fix them before running without --check."
  exit 1
fi

# ---------- 2. DataFlow framework -------------------------------------------
header "2/7 DataFlow Framework"

if "$PYTHON" -c "import dataflow" 2>/dev/null; then
  local_ver=$("$PYTHON" -c "import dataflow; print(getattr(dataflow, '__version__', 'unknown'))" 2>/dev/null)
  skip "DataFlow already installed (version: $local_ver)"
else
  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    warn "DataFlow not installed. Would install with: pip install open-dataflow"
  else
    info "Installing DataFlow framework..."
    "$PYTHON" -m pip install open-dataflow -q
    ok "DataFlow installed"
  fi
fi

# ---------- 3. Backend dependencies -----------------------------------------
header "3/7 Backend Python Dependencies"

REQUIREMENTS="$WEBUI_ROOT/backend/requirements.txt"
if [[ ! -f "$REQUIREMENTS" ]]; then
  err "backend/requirements.txt not found!"
  ERRORS=$((ERRORS + 1))
else
  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    info "Would install from $REQUIREMENTS"
  else
    info "Installing backend dependencies..."
    "$PYTHON" -m pip install -r "$REQUIREMENTS" -q
    ok "Backend dependencies installed"
  fi
fi

# ---------- 4. Frontend build -----------------------------------------------
header "4/7 Frontend Build"

FRONTEND_DIR="$WEBUI_ROOT/frontend"
if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
  err "frontend/package.json not found!"
  ERRORS=$((ERRORS + 1))
else
  if [[ -d "$FRONTEND_DIR/dist" ]] && [[ -f "$FRONTEND_DIR/dist/index.html" ]]; then
    skip "Frontend already built (frontend/dist/ exists)"
  else
    if [[ "$CHECK_ONLY" -eq 1 ]]; then
      info "Would run: npm install && npm run build in frontend/"
    else
      info "Installing frontend dependencies..."
      (cd "$FRONTEND_DIR" && npm install --silent 2>/dev/null)
      ok "npm packages installed"
      info "Building frontend..."
      (cd "$FRONTEND_DIR" && npm run build --silent 2>/dev/null)
      ok "Frontend built → frontend/dist/"
    fi
  fi
fi

# ---------- 5. DataFlow core init -------------------------------------------
header "5/7 DataFlow Core Initialization"

CORE_DIR="$WEBUI_ROOT/backend/data/dataflow_core"
if [[ -d "$CORE_DIR" ]] && [[ -n "$(ls -A "$CORE_DIR" 2>/dev/null)" ]]; then
  skip "DataFlow core already initialized ($CORE_DIR)"
else
  if [[ "$CHECK_ONLY" -eq 1 ]]; then
    info "Would initialize DataFlow core at $CORE_DIR"
  else
    info "Initializing DataFlow core..."
    mkdir -p "$CORE_DIR"
    (cd "$CORE_DIR" && "$PYTHON" -m dataflow init 2>/dev/null) || true
    ok "DataFlow core initialized"
  fi
fi

# ---------- 6. Agent MCP configuration --------------------------------------
header "6/7 Agent MCP Configuration"

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  info "Would run: ./scripts/setup_agent.sh all"
else
  bash "$SCRIPT_DIR/setup_agent.sh" all
fi

# ---------- 7. Summary ------------------------------------------------------
header "7/7 Setup Complete"

if [[ "$ERRORS" -gt 0 ]]; then
  err "$ERRORS error(s) encountered. Review the output above."
  exit 1
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  ok "All checks passed. Run without --check to install."
else
  ok "All done! Next steps:"
  info ""
  info "  1. Start the backend:"
  info "     ./scripts/start.sh"
  info "     # or: cd backend && uvicorn app.main:app --reload --port 8000 --host 0.0.0.0"
  info ""
  info "  2. Open the WebUI:"
  info "     http://localhost:8000/"
  info ""
  info "  3. For Cursor IDE users:"
  info "     Open this project in Cursor → Settings → MCP Servers → enable 'dataflow'"
  info ""
  info "  4. For Codex OAuth users (no API key):"
  info "     codex login"
  info ""
fi

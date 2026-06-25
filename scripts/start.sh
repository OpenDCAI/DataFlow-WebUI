#!/usr/bin/env bash
# start.sh — Start the DataFlow-WebUI backend server.
#
# Usage:
#   ./scripts/start.sh              # foreground (Ctrl+C to stop)
#   ./scripts/start.sh --daemon     # background (writes PID to .backend.pid)
#   ./scripts/start.sh --stop       # stop a backgrounded server
#   ./scripts/start.sh --status     # check if backend is running
#
# Prerequisites: run ./scripts/setup_all.sh first.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBUI_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$WEBUI_ROOT/backend"
PID_FILE="$WEBUI_ROOT/.backend.pid"
PORT="${DATAFLOW_PORT:-8000}"
HOST="${DATAFLOW_HOST:-0.0.0.0}"

# ---------- color helpers ---------------------------------------------------
if [[ -t 1 ]]; then
  C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_RED=$'\033[31m'
  C_BLUE=$'\033[34m'; C_BOLD=$'\033[1m'; C_RESET=$'\033[0m'
else
  C_GREEN=""; C_YELLOW=""; C_RED=""; C_BLUE=""; C_BOLD=""; C_RESET=""
fi

info()  { printf '%s[start]%s %s\n'            "$C_BLUE"   "$C_RESET" "$*"; }
ok()    { printf '%s[start]%s %sOK%s     %s\n' "$C_BLUE"   "$C_RESET" "$C_GREEN" "$C_RESET" "$*"; }
err()   { printf '%s[start]%s %sERROR%s  %s\n' "$C_BLUE"   "$C_RESET" "$C_RED"    "$C_RESET" "$*" >&2; }

# ---------- pre-flight checks ----------------------------------------------
preflight() {
  # Check Python can import the app
  if ! python3 -c "import sys; sys.path.insert(0,'$BACKEND_DIR'); import app.main" 2>/dev/null; then
    err "Cannot import app.main. Run ./scripts/setup_all.sh first."
    exit 1
  fi

  # Check if port is already in use
  if curl -sf "http://localhost:$PORT/api/v1/datasets/" >/dev/null 2>&1; then
    ok "Backend already running at http://localhost:$PORT"
    exit 0
  fi
}

# ---------- wait for ready --------------------------------------------------
wait_ready() {
  local max_wait=30
  local waited=0
  while [[ $waited -lt $max_wait ]]; do
    if curl -sf "http://localhost:$PORT/api/v1/datasets/" >/dev/null 2>&1; then
      ok "Backend ready at http://localhost:$PORT"
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  err "Backend did not become ready within ${max_wait}s"
  return 1
}

# ---------- commands --------------------------------------------------------
cmd_start_foreground() {
  preflight
  info "Starting backend (foreground) on $HOST:$PORT ..."
  info "Press Ctrl+C to stop."
  cd "$BACKEND_DIR"
  exec uvicorn app.main:app --reload --port "$PORT" --reload-dir app --host "$HOST"
}

cmd_start_daemon() {
  preflight
  info "Starting backend (daemon) on $HOST:$PORT ..."
  cd "$BACKEND_DIR"
  nohup uvicorn app.main:app --port "$PORT" --host "$HOST" \
    > "$WEBUI_ROOT/.backend.log" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"
  info "PID $pid written to .backend.pid"
  wait_ready
}

cmd_stop() {
  if [[ ! -f "$PID_FILE" ]]; then
    err "No .backend.pid found. Is the daemon running?"
    exit 1
  fi
  local pid
  pid=$(<"$PID_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    ok "Stopped backend (PID $pid)"
  else
    info "Process $pid already gone."
  fi
  rm -f "$PID_FILE"
}

cmd_status() {
  if curl -sf "http://localhost:$PORT/api/v1/datasets/" >/dev/null 2>&1; then
    ok "Backend is running at http://localhost:$PORT"
  else
    info "Backend is NOT running on port $PORT."
    exit 1
  fi
}

# ---------- dispatch --------------------------------------------------------
case "${1:-}" in
  --daemon|-d)   cmd_start_daemon ;;
  --stop)        cmd_stop ;;
  --status|-s)   cmd_status ;;
  --help|-h)
    echo "Usage: $0 [--daemon|--stop|--status]"
    echo "  (no flag)  Start in foreground"
    echo "  --daemon   Start in background"
    echo "  --stop     Stop background server"
    echo "  --status   Check if running"
    ;;
  *)             cmd_start_foreground ;;
esac

#!/usr/bin/env bash
# config.sh — the single place that defines runtime paths, ports and the
# package managers this project uses (plan items P1-06, P1-07).
#
# Docs and scripts must reference these values rather than restating them,
# so a port or package-manager change cannot leave the README stale.
#
# This file is only ever sourced, never executed. Every variable below is read
# by install.sh, configure_agent.sh or installers/lib/*.sh, which the linter
# cannot see from here — hence the file-wide SC2034 exemption. It is scoped to
# this file precisely because "assigned but never read" IS worth catching in
# ordinary scripts.
# shellcheck shell=bash
# shellcheck disable=SC2034

# ---------- service ---------------------------------------------------------
DF_PORT="${DATAFLOW_PORT:-8000}"
DF_MCP_PATH="/mcp"
DF_MCP_URL="${DATAFLOW_MCP_URL:-http://localhost:${DF_PORT}${DF_MCP_PATH}}"

# ---------- package managers (pinned) ---------------------------------------
# The repo tracks frontend/yarn.lock but every install path here uses npm.
# Resolved in favour of npm because build_release.sh and the release workflow
# already run npm, and yarn.lock carries platform-specific optional packages
# that break Linux release builds. Documented in docs/architecture/adr-002.
DF_NODE_PM="npm"
DF_NODE_PM_INSTALL_CMD="npm install --no-audit --no-fund"

# Python: pip into whatever environment is active. The installer deliberately
# does NOT create or activate a venv — that is the user's choice, and silently
# installing into a system Python is worse than saying nothing.
DF_PYTHON="${DATAFLOW_PYTHON:-python3}"

# ---------- paths -----------------------------------------------------------
# Where installed skills go. Project scope is the default so that installing
# writes inside the repo unless --scope user is given.
DF_SKILLS_USER_DIR="${DF_SKILLS_USER_DIR_OVERRIDE:-$HOME/.claude/skills}"
DF_SKILLS_PROJECT_DIR=".claude/skills"

# Receipt of what an install created, so --uninstall removes only that.
# One receipt per skills destination: a project-scope install and a user-scope
# install create different files, so uninstalling one cannot remove the other's
# skills. The suffix is a hash of the target path.
DF_RECEIPT_DIR=".dataflow-install"
DF_RECEIPT_REL=".dataflow-install-receipt"   # legacy single-receipt path

# Note: the backend's own runtime paths (data dir, dataflow_core, cache) are
# defined in backend/app/core/config.py and read from there. They were mirrored
# here once and never used, which is worse than not stating them at all — two
# declarations that can disagree.

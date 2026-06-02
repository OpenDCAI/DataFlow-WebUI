"""Factory + env-var-based config resolution for code-agent adapters.

The WebUI backend currently dispatches two agents headless: Claude Code
and Codex. Cursor is supported via its IDE (the user's Cursor session
connects to DataFlow through MCP and renders pipelines back to this UI);
the WebUI does not spawn ``cursor-agent`` as a subprocess. The
``CursorAdapter`` class is kept on disk for parity but is not registered
here.
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import AgentAdapter, AGENT_KINDS, DEFAULT_AGENT
from .claude_adapter import ClaudeAdapter
from .codex_adapter import CodexAdapter


_CLI_ENV_VARS = {
    "claude": ("DATAFLOW_CLAUDE_CLI", "claude"),
    "codex": ("DATAFLOW_CODEX_CLI", "codex"),
}


def resolve_cli_path(kind: str) -> str:
    env_var, default = _CLI_ENV_VARS[kind]
    return os.environ.get(env_var, "").strip() or default


def normalize_agent_kind(kind: str | None) -> str:
    if kind:
        kind = kind.strip().lower()
        if kind in AGENT_KINDS:
            return kind
    fallback = (
        os.environ.get("DATAFLOW_DEFAULT_AGENT", "").strip().lower()
        or DEFAULT_AGENT
    )
    return fallback if fallback in AGENT_KINDS else DEFAULT_AGENT


def get_adapter(
    kind: str,
    *,
    webui_root: Path,
    mcp_config_path: Path,
    system_prompt: str,
    allowed_tools: str,
) -> AgentAdapter:
    kind = normalize_agent_kind(kind)
    cli_path = resolve_cli_path(kind)
    common = dict(
        cli_path=cli_path,
        webui_root=webui_root,
        mcp_config_path=mcp_config_path,
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
    )
    if kind == "claude":
        return ClaudeAdapter(**common)
    if kind == "codex":
        return CodexAdapter(**common)
    raise ValueError(
        f"Unsupported headless agent kind: {kind!r}. "
        "Cursor users: connect Cursor IDE to DataFlow's MCP server via "
        ".cursor/mcp.json instead — see AGENT_SETUP.md."
    )

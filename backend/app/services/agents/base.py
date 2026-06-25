"""Common interface for code-agent adapters.

A NormalizedEvent is one of:
    {"type": "session", "session_id": "..."}        — emitted once per turn
    {"type": "text_chunk", "content": "..."}        — assistant text (streamed)
    {"type": "tool_call_start", "tool_use_id": "...", "name": "...", "input_preview": "..."}
    {"type": "tool_call_end", "tool_use_id": "...", "is_error": bool, "output_preview": "..."}
    {"type": "error", "message": "..."}             — adapter-level failure
    {"type": "done"}                                — turn complete

The endpoint forwards each of these to the frontend verbatim.
"""
from __future__ import annotations

import abc
import json
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

NormalizedEvent = dict[str, Any]

# Code agents that the WebUI backend dispatches headless via subprocess.
# Cursor is intentionally NOT in this list: Cursor's intended use is in the
# Cursor IDE itself, where the user's existing Cursor session connects to
# DataFlow via MCP (`.cursor/mcp.json`) and renders pipelines back into the
# WebUI through `mcp__dataflow__render_pipeline_in_editor`. There is no
# value in re-spawning `cursor-agent` as a headless subprocess from the
# backend. The CursorAdapter class is retained for parity / experimental use
# but the factory does not expose it.
AGENT_KINDS = ("claude", "codex")
DEFAULT_AGENT = "claude"


def truncate_preview(obj: Any, limit: int = 400) -> str:
    """Render any tool-call input/output as a short preview string."""
    try:
        s = json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj
    except Exception:
        s = str(obj)
    return s if len(s) <= limit else s[:limit] + "…"


class AgentAdapter(abc.ABC):
    """Wraps one code-agent CLI as an async stream of NormalizedEvent."""

    kind: str = ""  # subclasses set "claude" / "cursor" / "codex"

    def __init__(
        self,
        *,
        cli_path: str,
        webui_root: Path,
        mcp_config_path: Path,
        system_prompt: str,
        allowed_tools: str,
    ) -> None:
        self.cli_path = cli_path
        self.webui_root = webui_root
        self.mcp_config_path = mcp_config_path
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools

    @abc.abstractmethod
    async def chat_stream(
        self,
        message: str,
        *,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[NormalizedEvent, None]:
        """Run one turn, yield NormalizedEvent objects until `done`.

        ``session_id`` is the agent-specific session token from a previous turn.
        Implementations may ignore it (stateless agents) or pass it as a
        ``--resume``-style flag. The caller persists session ids per agent kind.
        """
        raise NotImplementedError
        yield  # pragma: no cover  — keep mypy happy: this is an async generator

    @abc.abstractmethod
    def kill(self) -> None:
        """Best-effort termination of the underlying subprocess (if any)."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_running(self) -> bool:
        """True if a subprocess is currently active for this adapter instance."""
        raise NotImplementedError

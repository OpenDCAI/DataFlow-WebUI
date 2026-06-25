"""Multi-agent adapter layer for DataFlow-WebUI.

Each adapter wraps a code-agent CLI (Claude Code, Cursor, Codex) and yields a
normalized stream of events that the WebSocket endpoint can forward to the
frontend without knowing which agent produced them.
"""
from .base import AgentAdapter, NormalizedEvent, AGENT_KINDS, DEFAULT_AGENT
from .factory import get_adapter

__all__ = [
    "AgentAdapter",
    "NormalizedEvent",
    "AGENT_KINDS",
    "DEFAULT_AGENT",
    "get_adapter",
]

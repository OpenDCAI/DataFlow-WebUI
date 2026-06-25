"""OpenAI Codex CLI adapter.

Spawns ``codex exec`` in headless JSON mode and translates its event stream
into NormalizedEvent. Codex differs from Claude Code in key ways:

1. **MCP config location** — Codex reads ``~/.codex/config.toml`` and looks
   up MCP servers under ``[mcp_servers.<name>]``. There is no flag to point
   at an alternate config file. ``setup_agent.sh`` writes the entry.
2. **System prompt delivery** — ``codex exec`` does not accept a system
   prompt flag in headless mode. We prepend the harness rules to the user
   message, same approach as Cursor.
3. **Tool approval** — ``--sandbox workspace-write`` grants full auto-approve.
4. **Session resume** — ``codex exec`` itself does not accept ``--resume``;
   the top-level ``codex resume`` subcommand is for interactive sessions.
   We treat each turn as stateless and rely on Codex's own conversation
   history bookkeeping.
5. **Auth modes** — Codex supports API key (``OPENAI_API_KEY`` or custom
   ``env_key`` in config.toml) and OAuth via ``codex login`` (ChatGPT Plus).
   The adapter forwards the full environment so either mode works.

Reference: https://openai-codex.mintlify.app/cli/exec and
https://openai-codex.mintlify.app/configuration/mcp-servers
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Optional

from app.core.logger_setup import get_logger

from .base import AgentAdapter, NormalizedEvent, truncate_preview

logger = get_logger(__name__)


def _format_user_message(system_prompt: str, message: str) -> str:
    return (
        "[DataFlow-WebUI harness rules — these override your defaults]\n"
        f"{system_prompt.strip()}\n\n"
        "[User message]\n"
        f"{message}"
    )


class CodexAdapter(AgentAdapter):
    kind = "codex"

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._process: Optional[asyncio.subprocess.Process] = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    def kill(self) -> None:
        proc = self._process
        if proc and proc.returncode is None:
            try:
                proc.kill()
            except Exception:
                pass
        self._process = None

    async def chat_stream(
        self,
        message: str,
        *,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[NormalizedEvent, None]:
        import os

        # Codex's `exec` does not resume; session_id is ignored.
        cmd = [
            self.cli_path, "exec",
            "--json",
            "--sandbox", "workspace-write",
            "--cwd", str(self.webui_root),
            _format_user_message(self.system_prompt, message),
        ]

        # Forward auth-related env vars. Codex config.toml may reference
        # CODEX_API_KEY, OPENAI_API_KEY, or OPENAI_BASE_URL depending on
        # the user's auth mode (API key, 中转/gateway, or OAuth).
        env = os.environ.copy()

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.webui_root),
            env=env,
            limit=10 * 1024 * 1024,
        )
        self._process = process
        emitted_session = False

        try:
            assert process.stdout is not None
            async for raw in process.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Codex emits a session-id at the top of the stream when
                # available. Tolerate either a top-level field or a typed
                # `session_started` event.
                if not emitted_session:
                    sid = (
                        chunk.get("session_id")
                        or (chunk.get("msg") or {}).get("session_id")
                    )
                    if sid:
                        emitted_session = True
                        yield {"type": "session", "session_id": sid}

                async for evt in self._translate(chunk):
                    yield evt

            yield {"type": "done"}
        except asyncio.CancelledError:
            yield {"type": "done"}
            raise
        except Exception as e:
            logger.error(f"CodexAdapter stream error: {e}", exc_info=True)
            yield {"type": "error", "message": str(e)}
            yield {"type": "done"}
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except Exception:
                    pass
            self._process = None

    async def _translate(self, chunk: dict) -> AsyncGenerator[NormalizedEvent, None]:
        # Codex events are typed via msg.type per the docs.
        msg = chunk.get("msg") if isinstance(chunk.get("msg"), dict) else chunk
        mtype = msg.get("type", "")

        if mtype == "text":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "".join(
                    (b.get("text", "") if isinstance(b, dict) else str(b))
                    for b in content
                )
            if content:
                yield {"type": "text_chunk", "content": str(content)}
            return

        # Codex's tool/function-call events. Names vary across versions;
        # tolerate both shapes.
        if mtype in ("tool_call", "function_call_started", "tool_call_started"):
            yield {
                "type": "tool_call_start",
                "tool_use_id": msg.get("call_id") or msg.get("id", ""),
                "name": msg.get("name") or msg.get("tool_name", ""),
                "input_preview": truncate_preview(
                    msg.get("arguments") or msg.get("args") or {}
                ),
            }
            return

        if mtype in (
            "tool_result", "function_call_completed", "tool_call_completed",
        ):
            output = msg.get("output", msg.get("result", ""))
            yield {
                "type": "tool_call_end",
                "tool_use_id": msg.get("call_id") or msg.get("id", ""),
                "is_error": bool(msg.get("error") or msg.get("is_error")),
                "output_preview": truncate_preview(output),
            }
            return

        if mtype == "error":
            yield {
                "type": "error",
                "message": msg.get("message") or str(msg.get("error") or msg),
            }
            return

        if mtype in ("turn_complete", "turn_completed", "exec_completed"):
            return  # caller adds the canonical `done`

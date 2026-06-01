"""Cursor CLI adapter.

Spawns ``cursor-agent`` in headless print mode and translates its stream-json
events into NormalizedEvent. Cursor differs from Claude Code in three ways
that matter here:

1. **MCP config location** — Cursor auto-reads ``.cursor/mcp.json`` from the
   workspace root. There is no equivalent of ``--mcp-config <path>``. Our
   ``setup_agent.sh`` writes the file before this adapter is ever used.
2. **System prompt delivery** — Cursor has no ``--append-system-prompt``
   flag. We prepend the system prompt to the user message instead.
3. **Tool approval** — Cursor's ``-p`` print mode auto-grants all tools.
   We pass ``-f`` (``--force``) to suppress any leftover approval prompts.

Reference: https://cursor.com/docs/cli/headless and
https://cursor.com/docs/cli/reference/parameters
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Optional

from app.core.logger_setup import get_logger

from .base import AgentAdapter, NormalizedEvent, truncate_preview

logger = get_logger(__name__)


def _format_user_message(system_prompt: str, message: str) -> str:
    """Embed the system prompt into the user message.

    Cursor has no system-prompt flag in headless mode, so the harness contract
    must travel inside the prompt itself. Skills loaded from ``.cursor/rules/``
    still apply automatically; this prepended block is for the per-WebUI rules
    that Claude Code receives via ``--append-system-prompt``.
    """
    return (
        "[DataFlow-WebUI harness rules — these override your defaults]\n"
        f"{system_prompt.strip()}\n\n"
        "[User message]\n"
        f"{message}"
    )


class CursorAdapter(AgentAdapter):
    kind = "cursor"

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
        cmd = [
            self.cli_path,
            "--print",
            "--output-format", "stream-json",
            "--stream-partial-output",
            "--force",
        ]
        if session_id:
            cmd += ["--resume", session_id]
        cmd.append(_format_user_message(self.system_prompt, message))

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.webui_root),
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

                # Cursor emits chat_id on the system/init event.
                ctype = chunk.get("type", "")
                if not emitted_session:
                    cid = chunk.get("chat_id") or chunk.get("session_id")
                    if cid:
                        emitted_session = True
                        yield {"type": "session", "session_id": cid}

                async for evt in self._translate(chunk):
                    yield evt

            yield {"type": "done"}
        except asyncio.CancelledError:
            yield {"type": "done"}
            raise
        except Exception as e:
            logger.error(f"CursorAdapter stream error: {e}", exc_info=True)
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
        ctype = chunk.get("type", "")
        subtype = chunk.get("subtype", "")

        if ctype == "system":
            return  # init metadata; nothing to forward

        if ctype == "assistant":
            # Per Cursor docs: streaming deltas have timestamp_ms but no
            # model_call_id. Buffered flushes have model_call_id and would
            # duplicate the streamed deltas if forwarded.
            if chunk.get("model_call_id") and chunk.get("timestamp_ms") is None:
                return
            text = ""
            msg = chunk.get("message", {}) or {}
            for block in msg.get("content", []) or []:
                if isinstance(block, dict) and block.get("type") in (None, "text"):
                    text += block.get("text", "")
            if not text and isinstance(msg.get("text"), str):
                text = msg["text"]
            if text:
                yield {"type": "text_chunk", "content": text}
            return

        if ctype == "tool_call":
            tc = chunk.get("tool_call", {}) or {}
            # Each tool surfaces as `<name>ToolCall` — pick the first match.
            tool_name = ""
            payload: dict = {}
            for key, value in tc.items():
                if isinstance(value, dict) and key.endswith("ToolCall"):
                    tool_name = key[: -len("ToolCall")]
                    payload = value
                    break
            tool_use_id = chunk.get("tool_call_id") or payload.get("id") or ""
            if subtype == "started":
                yield {
                    "type": "tool_call_start",
                    "tool_use_id": tool_use_id,
                    "name": tool_name,
                    "input_preview": truncate_preview(payload.get("args", {})),
                }
            elif subtype == "completed":
                result = payload.get("result", {})
                is_error = bool(result.get("error")) if isinstance(result, dict) else False
                output = result.get("success") if isinstance(result, dict) else result
                yield {
                    "type": "tool_call_end",
                    "tool_use_id": tool_use_id,
                    "is_error": is_error,
                    "output_preview": truncate_preview(output if output is not None else result),
                }
            return

        if ctype == "result":
            # Cursor's terminator. The outer loop will append `done` after stdout closes.
            err = chunk.get("error")
            if err:
                yield {"type": "error", "message": str(err)}

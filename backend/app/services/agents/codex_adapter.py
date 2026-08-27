"""OpenAI Codex CLI adapter.

Spawns ``codex exec`` in headless JSON mode and translates its event stream
into NormalizedEvent. Codex differs from Claude Code in key ways:

1. **MCP config location** — Codex reads ``~/.codex/config.toml`` and looks
   up MCP servers under ``[mcp_servers.<name>]``. There is no flag to point
   at an alternate config file, so there is no project-scoped Codex config.
   ``./install.sh configure-agent --agent codex --scope user`` writes the entry.
2. **System prompt delivery** — ``codex exec`` does not accept a system
   prompt flag in headless mode. We prepend the harness rules to the user
   message, same approach as Cursor.
3. **Tool approval** — ``--approve-for-me`` reviews headless tool calls
   automatically and applies Codex's workspace-write sandbox. Current Codex
   releases reject combining this flag with an explicit ``--sandbox`` value.
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
from collections import deque
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


def _build_exec_command(
    cli_path: str,
    webui_root: str,
    system_prompt: str,
    message: str,
) -> list[str]:
    """Build a command compatible with current headless Codex CLI releases."""
    return [
        cli_path,
        "exec",
        "--json",
        "--approve-for-me",
        "--cd",
        webui_root,
        _format_user_message(system_prompt, message),
    ]


def _format_process_error(returncode: int, stderr: str) -> str:
    """Turn a failed Codex invocation into a useful WebUI error."""
    detail = "\n".join(line for line in stderr.splitlines() if line.strip())
    if len(detail) > 1200:
        detail = detail[-1200:]
    if detail:
        return f"Codex exited with status {returncode}: {detail}"
    return f"Codex exited with status {returncode} without an error message."


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
        cmd = _build_exec_command(
            self.cli_path,
            str(self.webui_root),
            self.system_prompt,
            message,
        )

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
        emitted_error = False
        stderr_lines: deque[str] = deque(maxlen=40)

        async def drain_stderr() -> None:
            assert process.stderr is not None
            async for raw in process.stderr:
                line = raw.decode("utf-8", errors="replace").rstrip()
                if line:
                    stderr_lines.append(line)

        stderr_task = asyncio.create_task(drain_stderr())

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

                # Current Codex emits ``thread.started`` with ``thread_id``;
                # older builds used session_id in one of two shapes.
                if not emitted_session:
                    sid = (
                        chunk.get("thread_id")
                        or chunk.get("session_id")
                        or (chunk.get("msg") or {}).get("session_id")
                    )
                    if sid:
                        emitted_session = True
                        yield {"type": "session", "session_id": sid}

                async for evt in self._translate(chunk):
                    if evt.get("type") == "error":
                        emitted_error = True
                    yield evt

            returncode = await process.wait()
            await stderr_task
            if returncode != 0 and not emitted_error:
                yield {
                    "type": "error",
                    "message": _format_process_error(
                        returncode, "\n".join(stderr_lines)
                    ),
                }
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
            if not stderr_task.done():
                stderr_task.cancel()
            self._process = None

    async def _translate(self, chunk: dict) -> AsyncGenerator[NormalizedEvent, None]:
        # Codex 0.149+ uses top-level lifecycle events with an ``item`` payload.
        ctype = chunk.get("type", "")
        item = chunk.get("item") if isinstance(chunk.get("item"), dict) else {}
        item_type = item.get("type", "")

        if ctype == "item.completed" and item_type == "agent_message":
            text = item.get("text", "")
            if text:
                yield {"type": "text_chunk", "content": str(text)}
            return

        if ctype == "item.started" and item_type == "mcp_tool_call":
            server = item.get("server", "")
            tool = item.get("tool", "")
            name = f"mcp__{server}__{tool}" if server and tool else tool
            yield {
                "type": "tool_call_start",
                "tool_use_id": item.get("id", ""),
                "name": name,
                "input_preview": truncate_preview(item.get("arguments") or {}),
            }
            return

        if ctype == "item.completed" and item_type == "mcp_tool_call":
            error = item.get("error")
            yield {
                "type": "tool_call_end",
                "tool_use_id": item.get("id", ""),
                "is_error": bool(error),
                "output_preview": truncate_preview(error or item.get("result") or ""),
            }
            return

        if ctype == "item.started" and item_type == "command_execution":
            yield {
                "type": "tool_call_start",
                "tool_use_id": item.get("id", ""),
                "name": "command_execution",
                "input_preview": truncate_preview(item.get("command") or ""),
            }
            return

        if ctype == "item.completed" and item_type == "command_execution":
            exit_code = item.get("exit_code")
            yield {
                "type": "tool_call_end",
                "tool_use_id": item.get("id", ""),
                "is_error": exit_code not in (None, 0),
                "output_preview": truncate_preview(item.get("aggregated_output") or ""),
            }
            return

        if ctype in ("turn.failed", "error"):
            error = chunk.get("error")
            if isinstance(error, dict):
                message = error.get("message") or str(error)
            else:
                message = chunk.get("message") or str(error or chunk)
            yield {"type": "error", "message": message}
            return

        # Older Codex events were typed via msg.type. Keep accepting them so
        # the WebUI does not become tied to one narrow CLI release.
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

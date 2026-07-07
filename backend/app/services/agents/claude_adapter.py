"""Claude Code adapter.

Spawns the ``claude`` CLI with stream-json output and translates each chunk
into NormalizedEvent. The translation logic was previously inline in
``app/api/v1/endpoints/agent.py``; centralising it here so the endpoint can
treat Claude / Cursor / Codex uniformly.
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Optional

from app.core.logger_setup import get_logger

from .base import AgentAdapter, NormalizedEvent, truncate_preview

logger = get_logger(__name__)


class ClaudeAdapter(AgentAdapter):
    kind = "claude"

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
            "--print", message,
            "--output-format", "stream-json",
            "--verbose",
            # Emit partial message chunks (text_delta stream_events) as tokens
            # arrive, instead of only whole `assistant` blocks after each turn.
            # Without this the frontend receives text in one lump per turn and
            # the chat never appears to "stream". _translate() already handles
            # the stream_event/text_delta chunks. See buglog bug-004.
            "--include-partial-messages",
            "--mcp-config", str(self.mcp_config_path),
            "--append-system-prompt", self.system_prompt,
            "--allowedTools", self.allowed_tools,
            # acceptEdits (not dontAsk): dontAsk auto-approves MCP tools but
            # DENIES the built-in Write/Edit tools, so the agent cannot create
            # the dataset .jsonl files its skill requires — the turn then ends
            # empty with stop_reason=None. acceptEdits auto-accepts file edits
            # while keeping other guardrails, which fits this local pipeline-
            # building workflow. See buglog bug-003.
            "--permission-mode", "acceptEdits",
        ]
        if session_id:
            cmd += ["--resume", session_id]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.webui_root),
            limit=10 * 1024 * 1024,  # 10 MB, fits large MCP tool results
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

                # First chunk in a turn carries the canonical session_id.
                sid = chunk.get("session_id")
                if sid and not emitted_session:
                    emitted_session = True
                    yield {"type": "session", "session_id": sid}

                async for evt in self._translate(chunk):
                    yield evt

            yield {"type": "done"}
        except asyncio.CancelledError:
            yield {"type": "done"}
            raise
        except Exception as e:
            logger.error(f"ClaudeAdapter stream error: {e}", exc_info=True)
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
        """Translate a single Claude stream-json chunk into NormalizedEvent(s)."""
        ctype = chunk.get("type", "")

        if ctype == "stream_event":
            event = chunk.get("event", {})
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                text = delta.get("text", "")
                if text:
                    yield {"type": "text_chunk", "content": text}

        elif ctype == "assistant":
            for block in chunk.get("message", {}).get("content", []):
                btype = block.get("type")
                if btype == "text":
                    text = block.get("text", "")
                    if text:
                        yield {"type": "text_chunk", "content": text}
                elif btype == "tool_use":
                    yield {
                        "type": "tool_call_start",
                        "tool_use_id": block.get("id", ""),
                        "name": block.get("name", ""),
                        "input_preview": truncate_preview(block.get("input", {})),
                    }

        elif ctype == "user":
            for block in chunk.get("message", {}).get("content", []):
                if block.get("type") != "tool_result":
                    continue
                output = block.get("content", "")
                if isinstance(output, list):
                    output = "".join(
                        (b.get("text", "") if isinstance(b, dict) else str(b))
                        for b in output
                    )
                yield {
                    "type": "tool_call_end",
                    "tool_use_id": block.get("tool_use_id", ""),
                    "is_error": bool(block.get("is_error", False)),
                    "output_preview": truncate_preview(output),
                }

        elif ctype == "result":
            stop_reason = chunk.get("stop_reason", "")
            is_error = bool(chunk.get("is_error", False))
            result_text = chunk.get("result", "") or ""
            if (is_error or stop_reason in ("kvcache_no_enough", "max_turns_exceeded")) \
                    and not result_text.strip():
                hint = {
                    "kvcache_no_enough": "模型上下文/KV 缓存已塞满，Agent 中止。"
                                          "建议：清空对话重来，明确让 Agent 先调 "
                                          "list_operator_categories 再按类别拉算子。",
                    "max_turns_exceeded": "Agent 工具调用轮次达到上限。"
                                          "建议用更具体的指令或拆小需求再试。",
                }.get(stop_reason, f"Agent 异常结束（stop_reason={stop_reason}）")
                yield {"type": "error", "message": hint}

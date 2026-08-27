"""Compatibility checks for the headless Codex CLI adapter."""

import asyncio

from app.services.agents.codex_adapter import (
    CodexAdapter,
    _build_exec_command,
    _format_process_error,
)


def test_build_exec_command_uses_current_cli_flags(tmp_path):
    command = _build_exec_command(
        "codex",
        str(tmp_path),
        "system rules",
        "user request",
    )

    assert command[:6] == [
        "codex",
        "exec",
        "--json",
        "--approve-for-me",
        "--cd",
        str(tmp_path),
    ]
    assert "--sandbox" not in command
    assert command[6] == (
        "[DataFlow-WebUI harness rules — these override your defaults]\n"
        "system rules\n\n"
        "[User message]\n"
        "user request"
    )


def _translate(adapter, chunk):
    async def collect():
        return [event async for event in adapter._translate(chunk)]

    return asyncio.run(collect())


def test_translate_current_agent_message(tmp_path):
    adapter = CodexAdapter(
        cli_path="codex",
        webui_root=tmp_path,
        mcp_config_path=tmp_path / ".mcp.json",
        system_prompt="rules",
        allowed_tools="",
    )

    assert _translate(adapter, {
        "type": "item.completed",
        "item": {"id": "item_1", "type": "agent_message", "text": "你好！"},
    }) == [{"type": "text_chunk", "content": "你好！"}]


def test_translate_current_mcp_tool_lifecycle(tmp_path):
    adapter = CodexAdapter(
        cli_path="codex",
        webui_root=tmp_path,
        mcp_config_path=tmp_path / ".mcp.json",
        system_prompt="rules",
        allowed_tools="",
    )

    started = _translate(adapter, {
        "type": "item.started",
        "item": {
            "id": "item_2",
            "type": "mcp_tool_call",
            "server": "dataflow",
            "tool": "list_operator_categories",
            "arguments": {},
        },
    })
    completed = _translate(adapter, {
        "type": "item.completed",
        "item": {
            "id": "item_2",
            "type": "mcp_tool_call",
            "result": {"content": [{"type": "text", "text": "ok"}]},
            "error": None,
        },
    })

    assert started == [{
        "type": "tool_call_start",
        "tool_use_id": "item_2",
        "name": "mcp__dataflow__list_operator_categories",
        "input_preview": "{}",
    }]
    assert completed[0]["type"] == "tool_call_end"
    assert completed[0]["tool_use_id"] == "item_2"
    assert completed[0]["is_error"] is False
    assert '"text": "ok"' in completed[0]["output_preview"]


def test_format_process_error_includes_exit_status_and_stderr():
    message = _format_process_error(2, "first line\nargument conflict\n")

    assert "status 2" in message
    assert "argument conflict" in message


def test_chat_stream_surfaces_nonzero_exit_stderr(tmp_path):
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(
        "#!/bin/sh\n"
        "echo 'simulated CLI argument failure' >&2\n"
        "exit 2\n"
    )
    fake_codex.chmod(0o755)
    adapter = CodexAdapter(
        cli_path=str(fake_codex),
        webui_root=tmp_path,
        mcp_config_path=tmp_path / ".mcp.json",
        system_prompt="rules",
        allowed_tools="",
    )

    async def collect():
        return [event async for event in adapter.chat_stream("hello")]

    events = asyncio.run(collect())

    assert events[-1] == {"type": "done"}
    errors = [event for event in events if event["type"] == "error"]
    assert len(errors) == 1
    assert "status 2" in errors[0]["message"]
    assert "simulated CLI argument failure" in errors[0]["message"]

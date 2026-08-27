#!/usr/bin/env python3
"""Regression checks for the conservative Codex MCP config merger."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from installers.lib.codex_config import load_parser, merge


URL = "http://localhost:8000/mcp"
PYTHON = "/opt/dataflow/bin/python"


def parsed(text: str) -> dict:
    loads = load_parser()
    assert loads is not None, "a real TOML parser is required"
    return loads(text)


def check_new_bridge() -> None:
    out, code = merge('[mcp_servers.other]\nurl = "https://example.test/mcp"\n', URL, PYTHON, False)
    assert code == 0
    config = parsed(out)
    assert config["mcp_servers"]["other"]["url"] == "https://example.test/mcp"
    dataflow = config["mcp_servers"]["dataflow"]
    assert dataflow["command"] == PYTHON
    assert dataflow["args"] == ["-m", "mcp_proxy", URL]
    assert "url" not in dataflow


def check_legacy_url_migration() -> None:
    source = (
        '[mcp_servers.dataflow]\n'
        'url = "http://127.0.0.1:8000/mcp"\n'
        'enabled = false\n'
        'custom = "keep-me"\n'
    )
    out, code = merge(source, URL, PYTHON, False)
    assert code == 0
    dataflow = parsed(out)["mcp_servers"]["dataflow"]
    assert dataflow["command"] == PYTHON
    assert dataflow["args"] == ["-m", "mcp_proxy", URL]
    assert dataflow["enabled"] is False
    assert dataflow["custom"] == "keep-me"
    assert "url" not in dataflow


def check_equivalent_binary_bridge_is_preserved() -> None:
    source = (
        '[mcp_servers."dataflow"]\n'
        'command = "/custom/bin/mcp-proxy"\n'
        'args = ["http://127.0.0.1:8000/mcp"]\n'
        'tool_timeout_sec = 30\n'
    )
    out, code = merge(source, URL, PYTHON, False)
    assert code == 0
    dataflow = parsed(out)["mcp_servers"]["dataflow"]
    assert dataflow["command"] == "/custom/bin/mcp-proxy"
    assert dataflow["args"] == ["http://127.0.0.1:8000/mcp"]
    assert dataflow["tool_timeout_sec"] == 30


def check_conflict_and_force() -> None:
    source = (
        '[mcp_servers.dataflow]\n'
        'command = "foreign-server"\n'
        'args = ["--serve"]\n'
        'env = { TOKEN = "do-not-forward" }\n'
    )
    with redirect_stderr(io.StringIO()):
        _, code = merge(source, URL, PYTHON, False)
    assert code == 4

    out, code = merge(source, URL, PYTHON, True)
    assert code == 0
    dataflow = parsed(out)["mcp_servers"]["dataflow"]
    assert dataflow["command"] == PYTHON
    assert dataflow["args"] == ["-m", "mcp_proxy", URL]
    assert "env" not in dataflow


def check_invalid_and_inline_toml_are_refused() -> None:
    with redirect_stderr(io.StringIO()):
        _, code = merge("this is [not toml", URL, PYTHON, False)
    assert code == 3

    inline = f'mcp_servers = {{ dataflow = {{ url = "{URL}" }} }}\n'
    with redirect_stderr(io.StringIO()):
        _, code = merge(inline, URL, PYTHON, False)
    assert code == 4


def main() -> None:
    check_new_bridge()
    check_legacy_url_migration()
    check_equivalent_binary_bridge_is_preserved()
    check_conflict_and_force()
    check_invalid_and_inline_toml_are_refused()
    print("Codex MCP config checks passed")


if __name__ == "__main__":
    main()

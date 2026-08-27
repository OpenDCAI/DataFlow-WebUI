#!/usr/bin/env python3
"""Merge the DataFlow MCP entry into a Codex ``config.toml``, safely.

Codex reads only ``~/.codex/config.toml``. That file belongs to the user and may
hold settings and MCP servers this project knows nothing about, so:

* **A real parser, or nothing.** The file is parsed with ``tomllib`` (3.11+) or
  ``tomli``. If neither is importable, we refuse to write rather than guess with
  a hand-rolled parser — an approximate parser accepts files a real one rejects
  and silently corrupts them.
* **Never drop a key.** Keys inside the managed table that we do not own are
  preserved verbatim.
* **Bridge the legacy SSE endpoint.** Current Codex releases accept streamable
  HTTP URLs, while ``fastapi-mcp==0.4.0`` serves legacy SSE. The managed entry
  therefore launches ``mcp-proxy`` through the backend Python interpreter and
  talks to Codex over stdio.
* **Refuse ambiguity.** An existing ``dataflow`` server that points elsewhere,
  or that launches an unrelated command, is a real conflict. Redirecting it
  requires ``--force``. The URL form written by older DataFlow installers is
  migrated automatically when it points at the same endpoint.

Usage: codex_config.py <path> <url> <python-command> [--force]

Exit codes:
  0  merged content written to stdout
  2  no TOML parser available — cannot validate, so nothing is written
  3  file exists but is not valid TOML — caller must not write
  4  an existing dataflow entry conflicts — needs --force
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

MANAGED_KEY = "dataflow"
MANAGED_PREFIX = "mcp_servers"
DEFAULTS = {"enabled": "true", "tool_timeout_sec": "120"}

# A table header for the managed server, in any of TOML's equivalent spellings:
#   [mcp_servers.dataflow]   [mcp_servers."dataflow"]   [ mcp_servers . 'dataflow' ]
MANAGED_HEADER_RE = re.compile(
    r"""^\s*\[\s*mcp_servers\s*\.\s*(?:dataflow|"dataflow"|'dataflow')\s*\]\s*(?:\#.*)?$"""
)
ANY_HEADER_RE = re.compile(r"^\s*\[")
KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+|\"[^\"]*\"|'[^']*')\s*=\s*(.+?)\s*$")


def load_parser():
    """Return a ``loads`` callable, or None when no real TOML parser exists."""
    try:
        import tomllib
        return tomllib.loads
    except ModuleNotFoundError:
        pass
    try:
        import tomli
        return tomli.loads
    except ModuleNotFoundError:
        return None


def _bridge_values(python_command: str, url: str) -> tuple[str, list[str]]:
    return python_command, ["-m", "mcp_proxy", url]


def _urls_equivalent(left: str, right: str) -> bool:
    if left == right:
        return True
    try:
        a = urlsplit(left)
        b = urlsplit(right)
        loopback = {"localhost", "127.0.0.1", "::1"}
        return (
            a.scheme == b.scheme
            and a.hostname in loopback
            and b.hostname in loopback
            and a.port == b.port
            and a.path == b.path
            and a.query == b.query
            and a.fragment == b.fragment
        )
    except ValueError:
        return False


def _is_equivalent_bridge(existing: dict, python_command: str, url: str) -> bool:
    command = existing.get("command")
    args = existing.get("args")
    expected_command, expected_args = _bridge_values(python_command, url)
    if (
        command == expected_command
        and isinstance(args, list)
        and len(args) == 3
        and args[:2] == expected_args[:2]
        and isinstance(args[2], str)
        and _urls_equivalent(args[2], url)
    ):
        return True
    if isinstance(command, str) and Path(command).name in {"mcp-proxy", "mcp-proxy.exe"}:
        return (
            isinstance(args, list)
            and len(args) == 1
            and isinstance(args[0], str)
            and _urls_equivalent(args[0], url)
        )
    return False


def merge(text: str, url: str, python_command: str, force: bool) -> tuple[str, int]:
    loads = load_parser()
    if loads is None:
        sys.stderr.write(
            "no TOML parser available (need Python 3.11+, or `pip install tomli`).\n"
            "Refusing to edit config.toml without being able to validate it.\n"
        )
        return "", 2

    if text.strip():
        try:
            parsed = loads(text)
        except Exception as exc:
            sys.stderr.write(f"not valid TOML: {exc}\n")
            return "", 3
    else:
        parsed = {}

    servers = parsed.get(MANAGED_PREFIX)
    existing = servers.get(MANAGED_KEY) if isinstance(servers, dict) else None

    preserve_existing_bridge = False
    replacing_foreign_command = False
    if existing is not None:
        if not isinstance(existing, dict):
            sys.stderr.write(f"[{MANAGED_PREFIX}.{MANAGED_KEY}] is not a table\n")
            return "", 3
        current_url = existing.get("url")
        if "command" in existing:
            if _is_equivalent_bridge(existing, python_command, url):
                preserve_existing_bridge = True
            elif not force:
                sys.stderr.write(
                    f"existing [{MANAGED_PREFIX}.{MANAGED_KEY}] is a command/stdio server "
                    f"(command = {existing['command']!r}), not the DataFlow MCP bridge.\n"
                )
                return "", 4
            else:
                replacing_foreign_command = True
        elif (
            isinstance(current_url, str)
            and not _urls_equivalent(current_url, url)
            and not force
        ):
            sys.stderr.write(
                f"existing [{MANAGED_PREFIX}.{MANAGED_KEY}] points at {current_url!r}, "
                f"not {url!r}.\n"
            )
            return "", 4

    lines = text.splitlines()

    # Locate the managed table, accepting any spelling of its header.
    start = end = None
    for i, raw in enumerate(lines):
        if MANAGED_HEADER_RE.match(raw):
            if start is None:
                start = i
                end = None
        elif start is not None and end is None and ANY_HEADER_RE.match(raw):
            end = i
            break
    if start is not None and end is None:
        end = len(lines)

    if start is None:
        if existing is not None:
            sys.stderr.write(
                f"existing [{MANAGED_PREFIX}.{MANAGED_KEY}] uses an inline or "
                "otherwise unsupported TOML form; refusing to append a duplicate table.\n"
            )
            return "", 4
        out = list(lines)
        while out and not out[-1].strip():
            out.pop()
        if out:
            out.append("")
        out.append(f"[{MANAGED_PREFIX}.{MANAGED_KEY}]")
        command, args = _bridge_values(python_command, url)
        out.append(f"command = {json.dumps(command)}")
        out.append(f"args = {json.dumps(args)}")
        for key, value in DEFAULTS.items():
            out.append(f"{key} = {value}")
        return "\n".join(out) + "\n", 0

    # Rewrite in place, keeping the user's own header spelling and their keys.
    header = lines[start]
    body = lines[start + 1 : end]
    trailing_blanks = 0
    while body and not body[-1].strip():
        body.pop()
        trailing_blanks += 1

    if preserve_existing_bridge:
        bridge_command = existing["command"]
        bridge_args = existing["args"]
    else:
        bridge_command, bridge_args = _bridge_values(python_command, url)

    seen: set[str] = set()
    new_body: list[str] = []
    for raw in body:
        m = KEY_RE.match(raw)
        if not m:
            new_body.append(raw)
            continue
        key = m.group(1).strip("\"'")
        if key in {"url", "command", "args"}:
            continue
        if replacing_foreign_command and key == "env":
            continue
        seen.add(key)
        new_body.append(raw)
    new_body.insert(0, f"args = {json.dumps(bridge_args)}")
    new_body.insert(0, f"command = {json.dumps(bridge_command)}")
    for key, value in DEFAULTS.items():
        if key not in seen:
            new_body.append(f"{key} = {value}")

    out = lines[:start] + [header] + new_body
    out += [""] * trailing_blanks + lines[end:]
    merged = "\n".join(out) + "\n"

    # Never hand back something a parser would reject.
    try:
        loads(merged)
    except Exception as exc:  # pragma: no cover - guards against a rewrite bug
        sys.stderr.write(f"internal error: merge produced invalid TOML ({exc})\n")
        return "", 3

    return merged, 0


def main() -> int:
    if len(sys.argv) < 4:
        sys.stderr.write("usage: codex_config.py <path> <url> <python-command> [--force]\n")
        return 1
    path = Path(sys.argv[1])
    url = sys.argv[2]
    python_command = sys.argv[3]
    force = len(sys.argv) > 4 and sys.argv[4] == "--force"

    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    out, code = merge(text, url, python_command, force)
    if code != 0:
        return code
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

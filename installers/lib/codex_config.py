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
* **Refuse ambiguity.** An existing ``dataflow`` server that points elsewhere,
  or that is configured as a ``command``/stdio server rather than SSE, is a real
  conflict. Redirecting it requires ``--force``.

Usage: codex_config.py <path> <url> [--force]

Exit codes:
  0  merged content written to stdout
  2  no TOML parser available — cannot validate, so nothing is written
  3  file exists but is not valid TOML — caller must not write
  4  an existing dataflow entry conflicts — needs --force
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

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


def merge(text: str, url: str, force: bool) -> tuple[str, int]:
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

    if existing is not None:
        if not isinstance(existing, dict):
            sys.stderr.write(f"[{MANAGED_PREFIX}.{MANAGED_KEY}] is not a table\n")
            return "", 3
        current_url = existing.get("url")
        # A command/stdio server is a different transport, not a stale URL.
        # Merging our url into it would produce a hybrid config that is not a
        # valid server definition of either kind.
        if "command" in existing:
            if not force:
                sys.stderr.write(
                    f"existing [{MANAGED_PREFIX}.{MANAGED_KEY}] is a command/stdio server "
                    f"(command = {existing['command']!r}), not an SSE server.\n"
                    "Converting it would produce a mixed command+url definition.\n"
                )
                return "", 4
        elif isinstance(current_url, str) and current_url != url and not force:
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
        out = list(lines)
        while out and not out[-1].strip():
            out.pop()
        if out:
            out.append("")
        out.append(f"[{MANAGED_PREFIX}.{MANAGED_KEY}]")
        out.append(f'url = "{url}"')
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

    # With --force on a command/stdio entry, the transport keys must go: leaving
    # them beside url is the hybrid config we refuse to create.
    drop_keys = {"command", "args", "env"} if (existing and "command" in existing) else set()

    seen: set[str] = set()
    new_body: list[str] = []
    for raw in body:
        m = KEY_RE.match(raw)
        if not m:
            new_body.append(raw)
            continue
        key = m.group(1).strip("\"'")
        if key in drop_keys:
            continue
        seen.add(key)
        new_body.append(f'url = "{url}"' if key == "url" else raw)
    if "url" not in seen:
        new_body.insert(0, f'url = "{url}"')
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
    path = Path(sys.argv[1])
    url = sys.argv[2]
    force = len(sys.argv) > 3 and sys.argv[3] == "--force"

    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    out, code = merge(text, url, force)
    if code != 0:
        return code
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

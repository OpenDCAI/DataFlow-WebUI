#!/usr/bin/env python3
"""Merge the DataFlow MCP entry into a JSON MCP config (Claude, Cursor).

Same conservative rules as ``codex_config.py``:

* **Validate first** — an unparseable file is never rewritten.
* **Never drop a key** — other servers, and extra keys inside the ``dataflow``
  entry itself, are preserved.
* **Refuse ambiguity** — an existing ``dataflow`` entry pointing at a different
  URL may be deliberate, so redirecting it requires ``--force``.

Usage: mcp_json_config.py <path> <url> [--force]

Exit codes:
  0  merged JSON written to stdout
  3  file exists but is not usable JSON — caller must not write
  4  an existing dataflow entry points elsewhere — needs --force
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    path = Path(sys.argv[1])
    url = sys.argv[2]
    force = len(sys.argv) > 3 and sys.argv[3] == "--force"

    data: dict = {}
    if path.is_file():
        raw = path.read_text(encoding="utf-8")
        if raw.strip():
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError as exc:
                sys.stderr.write(f"{path} is not valid JSON ({exc.msg}, line {exc.lineno})\n")
                return 3
            if not isinstance(loaded, dict):
                sys.stderr.write(f"{path} does not contain a JSON object\n")
                return 3
            data = loaded

    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        sys.stderr.write(f"{path}: 'mcpServers' is not an object\n")
        return 3

    existing = servers.get("dataflow")
    if isinstance(existing, dict):
        current = existing.get("url")
        # A command/stdio server is a different transport, not a stale URL.
        # Adding our url beside it yields a hybrid that is neither.
        if "command" in existing:
            if not force:
                sys.stderr.write(
                    f"existing 'dataflow' server is a command/stdio server "
                    f"(command = {existing['command']!r}), not an SSE server.\n"
                    "Converting it would produce a mixed command+url definition.\n"
                )
                return 4
            entry = {
                k: v for k, v in existing.items()
                if k not in ("command", "args", "env", "type", "url")
            }
        elif isinstance(current, str) and current != url and not force:
            sys.stderr.write(
                f"existing 'dataflow' server points at {current!r}, not {url!r}.\n"
            )
            return 4
        else:
            # Preserve any extra keys the user added to this entry.
            entry = dict(existing)
        entry["type"] = "sse"
        entry["url"] = url
    else:
        if existing is not None:
            sys.stderr.write(f"{path}: 'mcpServers.dataflow' is not an object\n")
            return 3
        entry = {"type": "sse", "url": url}

    servers["dataflow"] = entry
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

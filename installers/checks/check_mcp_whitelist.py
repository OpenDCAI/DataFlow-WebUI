#!/usr/bin/env python3
"""Static check: the MCP tool whitelist and the FastAPI routes agree.

The MCP server exposes tools by naming FastAPI ``operation_id`` values in an
``include_operations`` list. Nothing enforces that those names exist, so a
renamed or deleted endpoint silently drops a tool from every agent's toolbox —
discovered only at runtime, when an agent calls a tool that isn't there.

This parses both sides with ``ast`` (no imports, so it runs without DataFlow or
FastAPI installed) and reports names that appear in one but not the other.

Exit 0 = consistent. Exit 1 = a whitelisted tool has no matching route.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MCP_SERVER = REPO_ROOT / "backend" / "app" / "mcp_server.py"
API_DIR = REPO_ROOT / "backend" / "app" / "api"

ROUTE_DECORATORS = {"get", "post", "put", "patch", "delete"}


def whitelisted_operations(path: Path) -> list[str]:
    """Pull the include_operations string list out of the FastApiMCP call."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "include_operations" and isinstance(kw.value, ast.List):
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        found.append(elt.value)
    return found


def declared_operation_ids(root: Path) -> dict[str, str]:
    """Map operation_id -> file:line for every route decorator in the tree."""
    out: dict[str, str] = {}
    files = list(root.rglob("*.py"))
    # The MCP module registers a route of its own (render_pipeline_in_editor).
    files.append(MCP_SERVER)
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            print(f"  ! cannot parse {path.relative_to(REPO_ROOT)}: {exc}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                attr = dec.func
                if not isinstance(attr, ast.Attribute) or attr.attr not in ROUTE_DECORATORS:
                    continue
                for kw in dec.keywords:
                    if kw.arg == "operation_id" and isinstance(kw.value, ast.Constant):
                        rel = path.relative_to(REPO_ROOT)
                        out[str(kw.value.value)] = f"{rel}:{node.lineno}"
    return out


def main() -> int:
    if not MCP_SERVER.is_file():
        print(f"[mcp-check] {MCP_SERVER} not found")
        return 1

    whitelist = whitelisted_operations(MCP_SERVER)
    if not whitelist:
        print("[mcp-check] FAIL: no include_operations whitelist found in mcp_server.py")
        return 1

    routes = declared_operation_ids(API_DIR)

    dupes = [name for name in set(whitelist) if whitelist.count(name) > 1]
    missing = [name for name in whitelist if name not in routes]

    if dupes:
        print(f"[mcp-check] FAIL: duplicated whitelist entries: {', '.join(sorted(dupes))}")
    if missing:
        print("[mcp-check] FAIL: whitelisted MCP tools with no matching route operation_id:")
        for name in missing:
            print(f"  - {name}")
        print("\n  An agent calling one of these gets 'tool not found' at runtime.")
        print("  Either add the operation_id to the endpoint or drop it from the whitelist.")

    if dupes or missing:
        return 1

    print(f"[mcp-check] OK — {len(whitelist)} MCP tools all resolve to real routes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

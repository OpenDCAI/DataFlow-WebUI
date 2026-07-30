"""Conditional-block renderer for canonical skill sources.

The canonical skill files under ``skills/canonical/`` are the single source of
truth. Agent-specific and profile-specific variants are *derived* from them by
this renderer, so a piece of guidance is written exactly once.

Directive syntax (in Markdown, so it stays invisible when rendered):

    <!-- @if profile==harness -->
    ...text only present in the harness/webui profiles...
    <!-- @elif agent==cursor -->
    ...
    <!-- @else -->
    ...
    <!-- @endif -->

Expressions are deliberately tiny: ``<var><op><literal>`` where ``op`` is
``==`` or ``!=``, joined by ``and`` / ``or``. There is no arbitrary eval.

Variable substitution uses ``{{@NAME}}`` and is resolved from the same context.
The ``@`` matters: skill templates use bare ``{{OP_NAME}}`` as author-facing
placeholders that must survive rendering untouched, so the renderer claims a
distinct syntax rather than competing for the same braces.
"""

from __future__ import annotations

import re
from typing import Any

IF_RE = re.compile(r"^\s*<!--\s*@(if|elif|else|endif)(?:\s+(.*?))?\s*-->\s*$")
VAR_RE = re.compile(r"\{\{@([A-Za-z0-9_]+)\}\}")
_TERM_RE = re.compile(r"^([a-z_][a-z0-9_]*)\s*(==|!=)\s*([A-Za-z0-9_.\-/]+)$")


class RenderError(ValueError):
    """Raised on malformed directives or unknown variables."""


def _eval_term(term: str, ctx: dict[str, Any]) -> bool:
    m = _TERM_RE.match(term.strip())
    if not m:
        raise RenderError(f"cannot parse condition term: {term!r}")
    var, op, literal = m.group(1), m.group(2), m.group(3)
    if var not in ctx:
        raise RenderError(f"unknown variable {var!r} in condition {term!r}")
    actual = str(ctx[var])
    return actual == literal if op == "==" else actual != literal


def _eval_expr(expr: str, ctx: dict[str, Any]) -> bool:
    """Evaluate ``a==b and c!=d`` / ``a==b or c==d``.

    Mixing ``and`` with ``or`` is rejected rather than silently assuming a
    precedence the author may not have intended.
    """
    expr = expr.strip()
    if not expr:
        raise RenderError("empty condition")
    has_and = re.search(r"\band\b", expr) is not None
    has_or = re.search(r"\bor\b", expr) is not None
    if has_and and has_or:
        raise RenderError(f"mixing 'and' with 'or' is not supported: {expr!r}")
    if has_or:
        return any(_eval_term(t, ctx) for t in re.split(r"\bor\b", expr))
    if has_and:
        return all(_eval_term(t, ctx) for t in re.split(r"\band\b", expr))
    return _eval_term(expr, ctx)


def substitute(text: str, ctx: dict[str, Any]) -> str:
    """Replace ``{{@NAME}}`` from ``ctx`` (case-insensitive key lookup).

    Bare ``{{NAME}}`` is left alone — those are skill-template placeholders.
    """
    lowered = {k.lower(): v for k, v in ctx.items()}

    def repl(m: re.Match[str]) -> str:
        key = m.group(1).lower()
        if key not in lowered:
            raise RenderError(f"unknown substitution variable {{{{@{m.group(1)}}}}}")
        return str(lowered[key])

    return VAR_RE.sub(repl, text)


def render(text: str, ctx: dict[str, Any]) -> str:
    """Resolve every ``@if`` block and ``{{VAR}}`` in ``text`` against ``ctx``."""
    out: list[str] = []
    # Each stack frame: [emitting_now, some_branch_already_taken, parent_emitting]
    stack: list[list[bool]] = []

    def emitting() -> bool:
        return all(frame[0] for frame in stack)

    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        m = IF_RE.match(line.rstrip("\n"))
        if not m:
            if emitting():
                out.append(line)
            continue

        kind, expr = m.group(1), m.group(2)
        try:
            if kind == "if":
                parent = emitting()
                taken = parent and _eval_expr(expr or "", ctx)
                stack.append([taken, taken, parent])
            elif kind == "elif":
                if not stack:
                    raise RenderError("@elif without @if")
                frame = stack[-1]
                if frame[1]:
                    frame[0] = False
                else:
                    frame[0] = frame[2] and _eval_expr(expr or "", ctx)
                    frame[1] = frame[1] or frame[0]
            elif kind == "else":
                if not stack:
                    raise RenderError("@else without @if")
                if expr:
                    raise RenderError(f"@else takes no condition, got {expr!r}")
                frame = stack[-1]
                frame[0] = frame[2] and not frame[1]
                frame[1] = True
            else:  # endif
                if not stack:
                    raise RenderError("@endif without @if")
                if expr:
                    raise RenderError(f"@endif takes no condition, got {expr!r}")
                stack.pop()
        except RenderError as exc:
            raise RenderError(f"line {lineno}: {exc}") from None

    if stack:
        raise RenderError(f"{len(stack)} unclosed @if block(s)")

    return substitute("".join(out), ctx)


def collapse_blank_runs(text: str) -> str:
    """Collapse 3+ consecutive blank lines left behind by stripped blocks."""
    return re.sub(r"\n{4,}", "\n\n\n", text)

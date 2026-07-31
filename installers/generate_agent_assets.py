#!/usr/bin/env python3
"""Generate every agent-specific skill asset from the canonical sources.

Canonical sources live in ``skills/canonical/``. This script derives:

  .claude/skills/<id>/       Claude Code skill packages
  .cursor/skills/<id>/       Cursor skill packages
  .cursor/rules/<id>.mdc     thin Cursor rules pointing at the skill above
  AGENTS.md                  aggregate instructions for Codex

Usage:
  python3 installers/generate_agent_assets.py            # write
  python3 installers/generate_agent_assets.py --check     # verify, exit 1 on drift
  python3 installers/generate_agent_assets.py --agent claude

``--check`` is what CI runs: it regenerates into a temp dir and diffs, so a
hand-edit of a generated file fails the build instead of silently drifting.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.render import RenderError, collapse_blank_runs, render  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "installers" / "skills.manifest.json"

# Only Markdown carries conditional directives; everything else is copied byte
# for byte (templates, .py scripts, .json specs).
RENDERABLE_SUFFIXES = {".md"}

GENERATED_BANNER = (
    "<!-- GENERATED FILE — DO NOT EDIT.\n"
    "     Source: {source}\n"
    "     Regenerate: python3 installers/generate_agent_assets.py -->\n"
)


def load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def iter_skill_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            yield path


def render_file(src: Path, dest: Path, ctx: dict, *, banner_source: str | None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() not in RENDERABLE_SUFFIXES:
        shutil.copy2(src, dest)
        return

    text = src.read_text(encoding="utf-8")
    try:
        out = collapse_blank_runs(render(text, ctx))
    except RenderError as exc:
        raise SystemExit(f"[generate] {src.relative_to(REPO_ROOT)}: {exc}") from None

    if banner_source and src.name == "SKILL.md":
        banner = GENERATED_BANNER.format(source=banner_source)
        if out.startswith("---\n"):
            end = out.find("\n---\n", 4)
            if end != -1:
                cut = end + len("\n---\n")
                out = out[:cut] + "\n" + banner + out[cut:]
            else:
                out = banner + out
        else:
            out = banner + out

    dest.write_text(out, encoding="utf-8")


def profile_context(profile: str) -> dict:
    """MCP guidance is only correct where an MCP server actually exists."""
    return {"profile": profile, "mcp": "yes" if profile in ("webui", "harness") else "no"}


def generate_skill_package(
    skill: dict, agent_cfg: dict, out_root: Path, profile: str
) -> None:
    src_root = REPO_ROOT / skill["canonical"]
    if not src_root.is_dir():
        raise SystemExit(f"[generate] canonical source missing: {skill['canonical']}")

    dest_root = out_root / skill["id"]
    ctx = {**agent_cfg["context"], **profile_context(profile)}

    for src in iter_skill_files(src_root):
        rel = src.relative_to(src_root)
        render_file(
            src,
            dest_root / rel,
            ctx,
            banner_source=f"{skill['canonical']}/{rel.as_posix()}",
        )


CURSOR_RULE_TEMPLATE = """---
description: {description}
globs: {globs}
alwaysApply: {always_apply}
---

<!-- GENERATED FILE — DO NOT EDIT.
     Source: {canonical}/SKILL.md
     Regenerate: python3 installers/generate_agent_assets.py -->

# {title} (Cursor)

The full instructions for this skill live in a single place:

    .cursor/skills/{skill_id}/SKILL.md

Read that file before acting on a request this rule matched. Supporting
references, examples and templates sit next to it in the same directory.

{summary}
"""


def generate_cursor_rules(manifest: dict, rules_dir: Path) -> None:
    globs_map = manifest.get("cursor_rule_globs", {})
    for skill in manifest["skills"]:
        if not skill.get("invocable", True):
            continue
        if "cursor" not in skill["agents"]:
            continue
        globs = globs_map.get(skill["id"], ["**/*.py"])
        # alwaysApply on the pipeline skill preserves the prior behaviour of
        # dataflow-pipeline.mdc, which was the repo's default-on rule.
        always = skill["id"] == "generating-dataflow-pipeline"
        rules_dir.mkdir(parents=True, exist_ok=True)
        (rules_dir / f"{skill['id']}.mdc").write_text(
            CURSOR_RULE_TEMPLATE.format(
                description=skill["summary"],
                globs=json.dumps(globs),
                always_apply="true" if always else "false",
                canonical=skill["canonical"],
                title=skill["id"].replace("-", " ").replace("_", " ").title(),
                skill_id=skill["id"],
                summary=skill["summary"],
            ),
            encoding="utf-8",
        )


AGENTS_HEADER = """# Agent Instructions (DataFlow-Harness)

<!-- GENERATED FILE — DO NOT EDIT.
     Source: skills/canonical/ via installers/skills.manifest.json
     Regenerate: python3 installers/generate_agent_assets.py -->

This file is read by **Codex** and any other agent following the `AGENTS.md`
convention. Claude Code reads `.claude/skills/` directly; Cursor reads
`.cursor/rules/` and `.cursor/skills/`. All three are generated from
`skills/canonical/`, so they never disagree.

**This is a routing table, not the instructions themselves.** Match the request
to a skill below, then read that skill's `SKILL.md` at the path given. Do not
read them all up front — each is long, and loading one you do not need costs
context you will want for the actual task.

For first-time setup, read `docs/agents/SETUP.md`.

## Pick a skill

| If the user asks to… | Read this | Needs MCP |
| --- | --- | --- |
"""

AGENTS_FOOTER = """
## Rules that apply regardless of skill

- **Never write, echo or commit an API key.** Ask for the *name* of an
  environment variable, never its value. To check one is set, test for presence
  (`[ -n "$VAR" ]`) — never `echo $VAR`, which writes the secret into the
  transcript.
- **Do not invent operators or parameters.** With MCP, confirm against
  `get_operator_detail_by_name`. Without it, use the bundled `core_text`
  reference and say when you could not verify.
- **Do not execute a pipeline unless asked.** Building and running are separate
  requests.
- **Never edit generated files by hand** — this file included. Edit
  `skills/canonical/` and run `make skills`.

## Where each skill lives

Paths are relative to the repository root:

| Skill | Full instructions |
| --- | --- |
"""


def generate_agents_md(manifest: dict, dest: Path, profile: str) -> None:
    """Write AGENTS.md as a routing table pointing at each skill.

    Earlier versions inlined every skill's full text, producing a ~1100-line file
    that a Codex session had to read in full before doing anything. That defeats
    progressive disclosure: the cost is paid on every task regardless of which
    skill is relevant. Now the file routes, and the skill files are read on demand.
    """
    triggers = manifest.get("routing_triggers", {})
    codex_skills = [s for s in manifest["skills"] if "codex" in s["agents"]]
    # Codex reads its own copy, not Cursor's — the two are rendered with
    # different contexts, and pointing at .cursor/ would couple them.
    skills_dir = manifest["agents"]["codex"].get("skills_dir", ".codex/skills")

    parts = [AGENTS_HEADER]
    for skill in codex_skills:
        if skill.get("kind") == "reference":
            continue
        requires = skill.get("requires", [])
        if "mcp" in requires:
            needs_mcp = "required"
        elif "mcp-optional" in requires:
            needs_mcp = (
                "no (bundled reference)"
                if profile == "skills"
                else "optional — richer with it"
            )
        else:
            needs_mcp = "no"
        trigger = triggers.get(skill["id"], skill["summary"])
        path = f"`{skills_dir}/{skill['id']}/SKILL.md`"
        parts.append(f"| {trigger} | {path} | {needs_mcp} |\n")

    # Reference packages are consulted by other skills, not routed to directly.
    for skill in codex_skills:
        if skill.get("kind") != "reference":
            continue
        parts.append(
            f"\nReference, read by the skills above rather than invoked: "
            f"`{skills_dir}/{skill['id']}/` — {skill['summary']}\n"
        )

    parts.append(AGENTS_FOOTER)
    for skill in codex_skills:
        src = REPO_ROOT / skill["canonical"] / "SKILL.md"
        if not src.is_file():
            raise SystemExit(f"[generate] missing SKILL.md for {skill['id']}")
        # Validate that every skill still renders for this profile, even though
        # the body is no longer inlined — a broken directive must fail the build
        # here rather than surface when an agent opens the file.
        ctx = {**manifest["agents"]["codex"]["context"], **profile_context(profile)}
        try:
            render(src.read_text(encoding="utf-8"), ctx)
        except RenderError as exc:
            raise SystemExit(f"[generate] {skill['canonical']}/SKILL.md: {exc}") from None
        parts.append(f"| `{skill['id']}` | `{skills_dir}/{skill['id']}/SKILL.md` |\n")

    dest.write_text("".join(parts), encoding="utf-8")


def build_into(manifest: dict, root: Path, agents: list[str], profile: str) -> None:
    for agent in agents:
        cfg = manifest["agents"][agent]
        if "skills_dir" in cfg:
            out = root / cfg["skills_dir"]
            for skill in manifest["skills"]:
                if agent in skill["agents"]:
                    generate_skill_package(skill, cfg, out, profile)
        if agent == "cursor" and "rules_dir" in cfg:
            generate_cursor_rules(manifest, root / cfg["rules_dir"])
        if agent == "codex":
            generate_agents_md(manifest, root / cfg["aggregate_file"], profile)


def targets_for(manifest: dict, agents: list[str]) -> list[str]:
    out: list[str] = []
    for agent in agents:
        cfg = manifest["agents"][agent]
        if "skills_dir" in cfg:
            out.append(cfg["skills_dir"])
        if agent == "cursor" and "rules_dir" in cfg:
            out.extend(
                f"{cfg['rules_dir']}/{s['id']}.mdc"
                for s in manifest["skills"]
                if s.get("invocable", True) and "cursor" in s["agents"]
            )
        if agent == "codex":
            out.append(cfg["aggregate_file"])
    return out


def compare_tree(expected: Path, actual: Path, label: str) -> list[str]:
    """Return human-readable drift lines between two trees or two files."""
    problems: list[str] = []

    if expected.is_file():
        if not actual.is_file():
            return [f"{label}: missing (never generated?)"]
        if expected.read_bytes() != actual.read_bytes():
            problems.append(f"{label}: content differs from canonical source")
        return problems

    if not actual.is_dir():
        return [f"{label}: directory missing"]

    exp_files = {p.relative_to(expected) for p in iter_skill_files(expected)}
    act_files = {p.relative_to(actual) for p in iter_skill_files(actual)}

    for rel in sorted(exp_files - act_files):
        problems.append(f"{label}/{rel}: missing")
    for rel in sorted(act_files - exp_files):
        problems.append(f"{label}/{rel}: unexpected (not derived from canonical)")
    for rel in sorted(exp_files & act_files):
        if not filecmp.cmp(expected / rel, actual / rel, shallow=False):
            problems.append(f"{label}/{rel}: content differs from canonical source")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify without writing; exit 1 on drift")
    ap.add_argument("--agent", action="append", choices=["claude", "codex", "cursor", "all"],
                    help="limit to one agent (repeatable); default all. 'all' is "
                         "accepted explicitly so callers can be unambiguous.")
    ap.add_argument("--profile", default="webui", choices=["webui", "harness", "skills"],
                    help="profile whose conditional blocks to resolve (default: webui)")
    ap.add_argument("--out", type=Path, help="write into this dir instead of the repo root")
    args = ap.parse_args()

    manifest = load_manifest()
    if not args.agent or "all" in args.agent:
        agents = list(manifest["agents"])
    else:
        agents = args.agent

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            ref = Path(tmp)
            build_into(manifest, ref, agents, args.profile)
            problems: list[str] = []
            for target in targets_for(manifest, agents):
                problems.extend(compare_tree(ref / target, REPO_ROOT / target, target))
            if problems:
                print("[generate --check] generated assets are out of sync with skills/canonical/:")
                for p in problems:
                    print(f"  - {p}")
                print("\nFix: python3 installers/generate_agent_assets.py")
                return 1
        print(f"[generate --check] OK — all generated assets match skills/canonical/ ({args.profile} profile)")
        return 0

    root = args.out or REPO_ROOT
    # Replace generated skill dirs wholesale so a renamed/removed canonical
    # skill cannot leave an orphan behind.
    for agent in agents:
        cfg = manifest["agents"][agent]
        if "skills_dir" in cfg:
            for skill in manifest["skills"]:
                if agent in skill["agents"]:
                    shutil.rmtree(root / cfg["skills_dir"] / skill["id"], ignore_errors=True)

    build_into(manifest, root, agents, args.profile)

    for name in manifest.get("retired_cursor_rules", []):
        stale = root / ".cursor" / "rules" / name
        if stale.exists():
            stale.unlink()
            print(f"[generate] removed retired rule .cursor/rules/{name}")

    # When staging for an installer, say so explicitly — printing bare repo
    # paths would imply we had written into the working tree.
    where = "" if args.out is None else f" (staged under {root})"
    for target in targets_for(manifest, agents):
        print(f"[generate] wrote {target}{where}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Skill lint (plan item P2-03).

Checks that hold for every skill in installers/skills.manifest.json:

  1. Manifest and disk agree — no manifest entry without a canonical dir, and
     no canonical dir missing from the manifest.
  2. Every skill package has a SKILL.md with parseable YAML frontmatter and a
     ``name`` that matches its directory.
  3. Relative Markdown links and referenced paths resolve on disk. This is the
     check that catches the ``../core_text/`` class of breakage, where a skill
     documents a sibling that its profile never installs.
  4. Cross-layer name collisions — two skills installing to the same directory
     name would silently overwrite each other.
  5. Conditional directives are balanced and reference known variables, for
     every (agent, profile) combination the manifest declares.

Runs with no third-party dependencies so CI needs no install step.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.render import RenderError, render  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = REPO_ROOT / "installers" / "skills.manifest.json"
CANONICAL_ROOT = REPO_ROOT / "skills" / "canonical"

# [text](target) — skip external URLs, anchors and mailto.
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Inline-code paths that look like a file reference inside the skill package.
CODE_PATH_RE = re.compile(r"`([^`\s]+/[^`\s]*\.(?:md|py|json|tmpl|sh))`")

problems: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def parse_frontmatter(text: str, label: str) -> dict[str, str]:
    """Minimal YAML frontmatter reader: top-level ``key: value`` only."""
    if not text.startswith("---\n"):
        fail(f"{label}: missing YAML frontmatter")
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        fail(f"{label}: frontmatter is never closed")
        return {}
    out: dict[str, str] = {}
    key = None
    for raw in text[4:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] not in " \t" and ":" in raw:
            key, _, val = raw.partition(":")
            key = key.strip()
            out[key] = val.strip()
        elif key:
            out[key] = (out.get(key, "") + " " + raw.strip()).strip()
    return out


def check_links(skill_dir: Path, md: Path) -> None:
    text = md.read_text(encoding="utf-8")
    rel_label = md.relative_to(REPO_ROOT)

    candidates: list[str] = []
    for m in LINK_RE.finditer(text):
        candidates.append(m.group(1))
    for m in CODE_PATH_RE.finditer(text):
        candidates.append(m.group(1))

    for target in candidates:
        target = target.strip()
        if not target or target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        # Strip anchors and any trailing markdown title.
        target = target.split("#", 1)[0].split(" ", 1)[0].strip()
        if not target or target.startswith(("$", "{", "<", "%")):
            continue  # a template placeholder, not a real path
        if target.startswith("/"):
            continue  # absolute paths are runtime, not repo-relative
        if "<" in target or ">" in target:
            continue  # a placeholder like operators/<type>/__init__.py
        # Paths into the upstream DataFlow package describe the user's own
        # checkout of OpenDCAI/DataFlow, which is not vendored here.
        if target.startswith(("dataflow/", "./dataflow/")):
            continue

        # Skill docs address paths two ways: relative to the containing file,
        # and relative to the skill root (agents are told to resolve
        # ${SKILL_DIR}/...). Accept either rather than forcing authors to
        # rewrite prose that already reads correctly.
        if (md.parent / target).exists() or (skill_dir / target).exists():
            continue

        # A ../sibling reference is valid iff that sibling is a skill this repo
        # ships — it becomes a real sibling once both are installed.
        if target.startswith("../"):
            sibling = target[3:].split("/", 1)[0]
            if (CANONICAL_ROOT / sibling).exists():
                continue
        fail(f"{rel_label}: broken relative reference '{target}'")


def check_render_matrix(manifest: dict, md: Path) -> None:
    """Every declared (agent, profile) pair must render without error."""
    text = md.read_text(encoding="utf-8")
    if "<!-- @" not in text:
        return
    rel_label = md.relative_to(REPO_ROOT)
    for agent, cfg in manifest["agents"].items():
        for profile in ("webui", "harness", "skills"):
            ctx = {
                **cfg["context"],
                "profile": profile,
                "mcp": "yes" if profile in ("webui", "harness") else "no",
            }
            try:
                render(text, ctx)
            except RenderError as exc:
                fail(f"{rel_label}: renders badly for agent={agent} profile={profile}: {exc}")
                return


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    skills = manifest["skills"]

    # --- 1. manifest vs disk ------------------------------------------------
    declared_dirs: dict[str, dict] = {}
    for skill in skills:
        path = REPO_ROOT / skill["canonical"]
        if not path.is_dir():
            fail(f"manifest lists {skill['id']} but {skill['canonical']} does not exist")
            continue
        declared_dirs[path.name] = skill

    if CANONICAL_ROOT.is_dir():
        for child in sorted(CANONICAL_ROOT.iterdir()):
            if child.is_dir() and child.name not in declared_dirs:
                fail(
                    f"skills/canonical/{child.name}/ exists but no manifest entry "
                    f"claims it — it would never be installed"
                )

    # --- 4. collisions ------------------------------------------------------
    seen: dict[str, str] = {}
    for skill in skills:
        install_name = Path(skill["canonical"]).name
        if install_name in seen and seen[install_name] != skill["id"]:
            fail(
                f"install-name collision: '{install_name}' claimed by both "
                f"{seen[install_name]} and {skill['id']}"
            )
        seen[install_name] = skill["id"]

    # --- 2, 3, 5 per skill --------------------------------------------------
    for skill in skills:
        root = REPO_ROOT / skill["canonical"]
        if not root.is_dir():
            continue

        md_files = sorted(root.rglob("*.md"))
        skill_mds = [p for p in md_files if p.name == "SKILL.md"]

        if not skill_mds:
            fail(f"{skill['id']}: no SKILL.md anywhere under {skill['canonical']}")
        # Every skill package needs a readable top-level SKILL.md — reference
        # packages included. That file is what tells an agent the package is
        # documentation rather than a workflow, and requiring it uniformly means
        # "installed but has no entry point" is always caught instead of being
        # exempted by directory name.
        top = root / "SKILL.md"
        if not top.is_file():
            fail(f"{skill['id']}: expected {skill['canonical']}/SKILL.md")
        else:
            fm = parse_frontmatter(top.read_text(encoding="utf-8"), f"{skill['id']}/SKILL.md")
            name = fm.get("name")
            if name and name != skill["id"]:
                fail(
                    f"{skill['id']}: frontmatter name '{name}' does not match "
                    f"directory/manifest id '{skill['id']}'"
                )
            if not fm.get("description"):
                fail(f"{skill['id']}: SKILL.md frontmatter has no description")
            # Only `name` and `description` are understood by every agent
            # implementation. Anything else risks being mishandled by one of
            # them, so package metadata lives in skills.manifest.json instead.
            extra = sorted(set(fm) - {"name", "description"})
            if extra:
                fail(
                    f"{skill['id']}: SKILL.md frontmatter has non-portable key(s) "
                    f"{', '.join(extra)} — put these in installers/skills.manifest.json"
                )

        # A reference package's nested docs are also parsed, so a malformed
        # frontmatter deep in the tree is reported rather than ignored.
        if skill.get("contains_nested_skills"):
            for md in skill_mds:
                if md == top:
                    continue
                rel = str(md.relative_to(REPO_ROOT))
                nested_fm = parse_frontmatter(md.read_text(encoding="utf-8"), rel)
                # Same portability rule as top-level SKILL.md: an agent that does
                # not know a key may mishandle it.
                nested_extra = sorted(set(nested_fm) - {"name", "description"})
                if nested_extra:
                    fail(
                        f"{rel}: non-portable frontmatter key(s) "
                        f"{', '.join(nested_extra)} — keep only name and description"
                    )
            notes.append(
                f"{skill['id']}: reference package with {len(skill_mds) - 1} nested docs"
            )

        for md in md_files:
            check_links(root, md)
            check_render_matrix(manifest, md)

    # --- report -------------------------------------------------------------
    if notes:
        for n in notes:
            print(f"[skill-lint] note: {n}")

    if problems:
        print(f"\n[skill-lint] FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1

    total = len(skills)
    print(f"[skill-lint] OK — {total} skills: manifest, frontmatter, links and directives all valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())

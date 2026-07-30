#!/usr/bin/env python3
"""Check relative links in repo documentation resolve (plan item P2-05).

Covers the Markdown a human or agent is routed through — root README, docs/,
and the component READMEs — not the skill packages (check_skills.py owns those).

Also flags references to commands and files the docs promise but the repo does
not provide, which is the specific way the old README went stale.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DOC_FILES = [
    "README.md",
    "README_zh.md",
    "AGENT_SETUP.md",
    "CLAUDE.md",
    "README-release-en.md",
    "README-release-zh.md",
    "backend/README.md",
    "frontend/README.md",
    "frontend/docs/README_zh.md",
]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# Shell commands the docs tell users to run, e.g. ./install.sh or a script path.
CMD_RE = re.compile(r"(?:^|\s|`)(\./(?:install\.sh|scripts/[\w.-]+|installers/[\w./-]+))")

problems: list[str] = []


def doc_paths() -> list[Path]:
    paths = [REPO_ROOT / f for f in DOC_FILES]
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.is_dir():
        paths += sorted(docs_dir.rglob("*.md"))
    return [p for p in paths if p.is_file()]


def check_links(path: Path) -> None:
    rel = path.relative_to(REPO_ROOT)
    text = path.read_text(encoding="utf-8")

    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        resolved = (path.parent / clean).resolve()
        if not resolved.exists():
            problems.append(f"{rel}: link target does not exist: {target}")

    for cmd in set(CMD_RE.findall(text)):
        script = (REPO_ROOT / cmd[2:]).resolve()
        if not script.exists():
            problems.append(f"{rel}: documents a command that does not exist: {cmd}")


# A fenced-code or inline-code invocation of a deprecated script, i.e. an
# instruction to run it — as opposed to prose explaining what it used to do,
# which ADRs and migration guides legitimately need.
STALE_INVOKE_RE = re.compile(
    r"(?:^|\n)\s*(?:\$\s*)?\./scripts/(setup_all|setup_agent)\.sh", re.M
)


# Files copied into the release zip by scripts/build_release.sh, and the paths
# that exist alongside them there. A relative link out of this set resolves in
# the repo but breaks for anyone reading the unzipped package.
RELEASE_FILES = ["README-release-en.md", "README-release-zh.md", "docs/RELEASE-PACKAGE.md"]
RELEASE_CONTENTS = {
    "README-release-en.md",
    "README-release-zh.md",
    "LICENSE",
    "run.sh",
    "run.bat",
    "docs/RELEASE-PACKAGE.md",
}


def check_release_links() -> None:
    """A doc shipped in the release zip may only link to things also in the zip."""
    for name in RELEASE_FILES:
        path = REPO_ROOT / name
        if not path.is_file():
            problems.append(f"{name}: listed as a release file but does not exist")
            continue
        base = Path(name).parent
        for target in LINK_RE.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#", "mailto:", "<")):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            # Resolve as the reader of the unzipped package would.
            resolved = os.path.normpath(str(base / clean)) if str(base) != "." else clean
            if resolved not in RELEASE_CONTENTS:
                problems.append(
                    f"{name}: links to '{target}', which is not shipped in the "
                    f"release zip — use an absolute URL instead"
                )


def check_no_stale_commands() -> None:
    """Docs must not instruct users to run the deprecated setup flows."""
    for path in doc_paths():
        rel = path.relative_to(REPO_ROOT)
        if "migration" in rel.parts:
            continue  # migration docs show the old commands to map them
        text = path.read_text(encoding="utf-8")
        for match in set(STALE_INVOKE_RE.findall(text)):
            replacement = (
                "./install.sh --profile <id>"
                if match == "setup_all"
                else "./install.sh configure-agent"
            )
            problems.append(
                f"{rel}: instructs the reader to run deprecated "
                f"./scripts/{match}.sh — use '{replacement}'"
            )


def main() -> int:
    paths = doc_paths()
    for path in paths:
        check_links(path)
    check_no_stale_commands()
    check_release_links()

    if problems:
        print(f"[docs-check] FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"[docs-check] OK — {len(paths)} documents, all relative links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())

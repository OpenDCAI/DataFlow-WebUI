#!/usr/bin/env python3
"""Validate the profile manifests install.sh executes.

install.sh evals the ``run`` / ``skip_if`` strings from these JSON files, so a
typo there becomes a runtime shell error mid-install. This checks structure and
cross-references before that can happen:

  1. Required keys are present and non-empty.
  2. Every ``run``/``skip_if``/``verify`` command names a df_* function that
     actually exists in installers/lib/, or is a plain interpreter call.
  3. Every skill layer a profile requests exists in skills.manifest.json.
  4. The three profiles' claims stay consistent with each other — notably that
     only webui touches Node, and that skills installs no packages.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROFILE_DIR = REPO_ROOT / "installers" / "profiles"
SKILLS_MANIFEST = REPO_ROOT / "installers" / "skills.manifest.json"
LIB_DIR = REPO_ROOT / "installers" / "lib"

REQUIRED_KEYS = [
    "id", "label", "description", "audience", "installs", "does_not_install",
    "writes_outside_repo", "prerequisites", "skill_layers", "steps", "verify",
    "must_not_touch", "next_steps",
]

FUNC_RE = re.compile(r"^([a-z_][a-z0-9_]*)\s*\(\)", re.M)
DF_CALL_RE = re.compile(r"\b(df_[a-z0-9_]+)\b")

problems: list[str] = []


def defined_functions() -> set[str]:
    names: set[str] = set()
    for path in sorted(LIB_DIR.glob("*.sh")):
        names |= set(FUNC_RE.findall(path.read_text(encoding="utf-8")))
    return names


def main() -> int:
    funcs = defined_functions()
    skills_manifest = json.loads(SKILLS_MANIFEST.read_text(encoding="utf-8"))
    # The declared vocabulary, not just the layers currently in use: a profile
    # may legitimately request a layer that has no skills in it yet.
    known_layers = set(skills_manifest.get("layers", []))
    used_layers = {s["layer"] for s in skills_manifest["skills"]}
    for layer in sorted(used_layers - known_layers):
        problems.append(
            f"skills.manifest.json: a skill uses layer '{layer}' which is not in "
            f"the declared 'layers' list"
        )

    profiles: dict[str, dict] = {}
    for path in sorted(PROFILE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        profiles[data.get("id", path.stem)] = data

        if data.get("id") != path.stem:
            problems.append(f"{path.name}: id '{data.get('id')}' does not match filename")

        for key in REQUIRED_KEYS:
            if key not in data:
                problems.append(f"{path.name}: missing required key '{key}'")
            elif isinstance(data[key], (list, str)) and not data[key]:
                problems.append(f"{path.name}: '{key}' is empty")

        for layer in data.get("skill_layers", []):
            if layer not in known_layers:
                problems.append(
                    f"{path.name}: skill_layers references unknown layer '{layer}' "
                    f"(known: {', '.join(sorted(known_layers))})"
                )

        # Every df_* referenced must exist, or install.sh dies mid-run.
        commands: list[tuple[str, str]] = []
        for step in data.get("steps", []):
            for field in ("run", "skip_if"):
                if step.get(field):
                    commands.append((f"steps[{step.get('id')}].{field}", step[field]))
        for v in data.get("verify", []):
            commands.append((f"verify[{v.get('id')}].run", v["run"]))

        for where, cmd in commands:
            for name in DF_CALL_RE.findall(cmd):
                if name not in funcs:
                    problems.append(
                        f"{path.name}: {where} calls '{name}', which is not defined "
                        f"in installers/lib/*.sh"
                    )

        for step in data.get("steps", []):
            for key in ("id", "label", "run"):
                if not step.get(key):
                    problems.append(f"{path.name}: a step is missing '{key}'")

    # --- cross-profile invariants ------------------------------------------
    if "harness" in profiles:
        blob = json.dumps(profiles["harness"])
        if "npm" in blob or "node" in blob.lower().replace("node-", ""):
            for step in profiles["harness"]["steps"]:
                if "npm" in step["run"] or "frontend" in step["run"]:
                    problems.append(
                        "harness.json: a step touches Node/frontend — this profile "
                        "must install on a machine with no Node.js"
                    )
        guarded = profiles["harness"]["must_not_touch"]
        if not any(p.startswith("frontend") for p in guarded):
            problems.append(
                "harness.json: must_not_touch must guard some frontend path — "
                "this profile has to install with no Node.js present"
            )
        if "node_modules" not in guarded:
            problems.append("harness.json: must_not_touch should list 'node_modules'")

    if "skills" in profiles:
        for step in profiles["skills"]["steps"]:
            if "pip" in step["run"]:
                problems.append(
                    "skills.json: a step runs pip — this profile must install no packages"
                )
        for forbidden in ("~/.codex/config.toml", "~/.cursor/mcp.json"):
            if forbidden not in profiles["skills"]["must_not_touch"]:
                problems.append(f"skills.json: must_not_touch should list '{forbidden}'")

    for pid, data in profiles.items():
        # Installing must never write agent config implicitly (plan D-06).
        for step in data.get("steps", []):
            if "configure_agent" in step["run"]:
                problems.append(
                    f"{pid}.json: step '{step['id']}' runs the agent configurator; "
                    f"agent config must stay an explicit separate command"
                )

    if problems:
        print(f"[profile-check] FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"[profile-check] OK — {len(profiles)} profiles valid ({', '.join(sorted(profiles))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

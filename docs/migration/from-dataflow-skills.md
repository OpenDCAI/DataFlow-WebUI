# Migrating from `OpenDCAI/DataFlow-Skills`

The standalone skills now live in this repository. `DataFlow-Skills` is now a
compatibility bridge, not a second source of skill content. Its `install.sh`
delegates to this repository's `--profile skills` installer, using a sibling
WebUI checkout when available or cloning the selected WebUI ref temporarily.

## If you installed from the old repo

Old:

```bash
git clone https://github.com/OpenDCAI/DataFlow-Skills.git
cd DataFlow-Skills
./install.sh
```

New:

```bash
git clone https://github.com/OpenDCAI/DataFlow-WebUI.git
cd DataFlow-WebUI
./install.sh --profile skills
```

Same skill names, so your `/generating-dataflow-pipeline` and `/dataflow-dev`
invocations keep working.

**The default destination changed.** The old installer defaulted to
`~/.claude/skills/`; this one defaults to `./.claude/skills/` inside the repo, so
installing does not write to your home directory unless you ask. Pass
`--scope user` for the old behaviour.

Flag mapping:

| Old | New |
|---|---|
| `./install.sh` | `./install.sh --profile skills` |
| `./install.sh --project` | `./install.sh --profile skills --scope project` (now the default) |
| `./install.sh --user` | `./install.sh --profile skills --scope user` |
| `./install.sh --force` | `./install.sh --profile skills --force` |
| `./install.sh dataflow-dev` | *no per-skill selection — see below* |

### Per-skill installation

The old installer took skill names. The new one installs a profile's whole set,
because the pipeline skill reads `core_text` and shipping one without the other
produces broken references. If you need a subset, copy it yourself:

```bash
python3 installers/generate_agent_assets.py --profile skills --agent claude --out /tmp/staged
cp -R /tmp/staged/.claude/skills/dataflow-dev ~/.claude/skills/
```

## What you gain

**`core_text` references now resolve.** The old repo's pipeline skill pointed at
`../core_text/`, which worked there. This repo's copy had the same references
with no `core_text` directory — six broken links. `core_text` is now imported
here, so both are correct.

**Two more skills.** `dataflow-operator-builder` and `prompt-template-builder`
only ever existed in this repo.

**MCP-aware content, when you want it.** The old `generating-dataflow-pipeline`
had no MCP guidance. The canonical version now carries it conditionally: the
`skills` profile strips it (identical in spirit to what you had), while `harness`
and `webui` include the rules for validating and committing pipelines through
MCP. One file, no divergence — see
[ADR-001](../architecture/adr-001-source-of-truth.md).

## Content differences to be aware of

The imported skills are a superset of the old ones, with two intentional edits:

- **`dataflow-dev` lost its "WebUI 变更策略" section.** It duplicated repo
  governance and contradicted this repo's `CLAUDE.md`, which had already relaxed
  the policy it described. Repo rules belong in `CLAUDE.md`, not in a
  distributable skill.
- **`known_issues.md` gained Issue #009** (`json_schema` missing
  `additionalProperties: false` → API 500 with infinite retries). It was in this
  repo's copy and not the old one.

## Old clone URL

The old README pointed at `haolpku/DataFlow-Skills`, while the org repo is
`OpenDCAI/DataFlow-Skills`. Neither is the source of truth now; use
`OpenDCAI/DataFlow-WebUI`.

## History

This import is a content snapshot, not a history graft: the commit history of
`DataFlow-Skills` stays in that repository for old clone URLs. Its historical
files remain available for provenance, but the compatibility installer is the
only supported entry point and no new skill changes should be made there. If
full history is wanted here later, that should be a dedicated `git subtree`
import PR.

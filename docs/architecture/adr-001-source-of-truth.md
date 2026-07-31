# ADR-001: One source of truth for skills

- Status: **accepted**
- Date: 2026-07-29
- Supersedes: the informal arrangement where `OpenDCAI/DataFlow-Skills` and this
  repo both carried hand-maintained copies of the same skills

| Scope | Status |
|---|---|
| Within this repo: `skills/canonical/` is the only hand-edited source; agent assets are generated | **accepted** — implemented and enforced by CI |
| The fate of the external `OpenDCAI/DataFlow-Skills` repo | **accepted** — compatibility bridge to this repo's `skills` profile; no independent skill source |

`DataFlow-Skills` remains available for old clone URLs, but its installer now
delegates to this repository's `skills` profile. Its historical skill files are
not an alternate source and must not receive new fixes.

## Context

The same skills existed in two repositories and, within this repository, in
several places at once:

- `OpenDCAI/DataFlow-Skills` shipped `generating-dataflow-pipeline`,
  `dataflow-dev` and `core_text`
- this repo shipped its own `generating-dataflow-pipeline` and `dataflow-dev`
  under `.claude/skills/`, plus `dataflow-operator-builder` and
  `prompt-template-builder`
- `.cursor/skills/` held a second copy of all four
- `.cursor/rules/` held hand-written condensations of three of them
- `AGENTS.md` was generated from one of them by `scripts/setup_agent.sh`

They had already diverged. Measured at the time of this decision:

- all four `SKILL.md` files differed between `.claude/skills/` and
  `.cursor/skills/`; the Cursor copies were missing MCP rules that had been added
  to the Claude copies, including "call `validate_pipeline_config` before
  create/update" and the `init` vs `run` parameter-bucket rules
- this repo's `generating-dataflow-pipeline` had 111 lines the `DataFlow-Skills`
  copy lacked
- `dataflow-dev` in this repo carried a "WebUI change policy" section that
  contradicted `CLAUDE.md`, which had since relaxed exactly that policy
- this repo's pipeline skill referenced `../core_text/` in six places while no
  `core_text` directory existed here — every one of those references was broken

Divergence of instructions is not cosmetic. An agent reading the Cursor copy
skipped validation that the Claude copy required, which produces pipelines that
fail at execution rather than at creation.

## Decision

**This repository's `skills/canonical/` is the only hand-edited source of skill
content.** Everything else is generated:

```
skills/canonical/            ← edit here, and only here
  ├── generating-dataflow-pipeline/
  ├── dataflow-dev/
  ├── dataflow-operator-builder/
  ├── prompt-template-builder/
  └── core_text/             ← imported from DataFlow-Skills

     │  installers/generate_agent_assets.py
     ▼
.claude/skills/   .cursor/skills/   .cursor/rules/*.mdc   .codex/skills/   AGENTS.md
```

Variation between agents and profiles is expressed *inside* the canonical file
with conditional directives, rather than by keeping divergent copies:

```markdown
<!-- @if mcp==yes -->
Call `validate_pipeline_config` before create/update.
<!-- @endif -->
```

Two variables drive it: `mcp` (`yes` for the webui/harness profiles, `no` for
skills) and per-agent flags such as `structured_questions` and `slash_commands`.
So the MCP validation rule is written once and reaches every agent that has MCP,
which is precisely what failed before.

CI runs `generate_agent_assets.py --check`, which regenerates into a temp
directory and diffs. A hand-edit of a generated file fails the build.

Its `core_text` content is imported here (71 files), which also fixes the six
broken `../core_text/` references.

**Compatibility bridge:** `OpenDCAI/DataFlow-Skills` carries a migration notice
and a wrapper that invokes `DataFlow-WebUI/install.sh --profile skills`. A local
`../DataFlow-WebUI` checkout is preferred; otherwise the wrapper clones a
selected WebUI ref temporarily. This keeps the old entry point usable while
ensuring the installed output comes from the current canonical source.

## Alternatives rejected

**Keep `DataFlow-Skills` as the source and sync inward.** The MCP-aware guidance
has no meaning without this repo's MCP server, so the interesting content would
still originate here. Two-way sync between two writable repos is what caused the
drift.

**Generate nothing; require editors to update all copies.** This was the previous
arrangement. It failed — every file had drifted.

**One skill per agent, maintained separately.** Honest about the differences but
multiplies real guidance by three; the MCP rules that went missing from Cursor
are exactly what this loses.

## Consequences

Good:

- guidance is written once; agent and profile differences are explicit and
  reviewable in one file
- CI makes drift impossible rather than merely discouraged
- the `skills` profile can ship a coherent MCP-free variant automatically
- broken cross-skill references are caught by `installers/checks/check_skills.py`

Costs:

- contributors must learn to edit `skills/canonical/` and regenerate. The
  generated files carry a `GENERATED FILE — DO NOT EDIT` banner naming their
  source, and CI names the file and the fix command
- conditional directives make canonical files slightly harder to read than a
  finished one
- users of the old `DataFlow-Skills` clone URL are redirected by the bridge

## Verification

```bash
python3 installers/generate_agent_assets.py --check   # generated == canonical
python3 installers/checks/check_skills.py             # frontmatter, links, directives
```

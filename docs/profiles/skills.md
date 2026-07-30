# Profile: `skills`

Agent skills for writing DataFlow pipelines by hand. No server, no MCP, no packages.

```bash
./install.sh --profile skills
```

## What this is for

You want Claude Code, Codex or Cursor to write *correct* DataFlow code — right operators, right parameter names, right field ordering — and you are happy running `python pipeline.py` yourself.

## What this is not for

- Seeing pipelines as a graph → use [`webui`](webui.md)
- Letting the agent query your actual installed operator registry, validate a pipeline before committing, or execute it → use [`harness`](harness.md)

The skills here carry a *bundled* operator reference. It is accurate for the DataFlow version it was written against, but it is a snapshot, not a live query.

## Prerequisites

Python 3.9+ — used only to render the skill files. Nothing is installed into it.

An agent that can read the installed instructions. All three are supported, but
they read from different places — see the table below.

## Install

```bash
./install.sh --profile skills                    # into ./.claude/skills (this repo only)
./install.sh --profile skills --scope user       # into ~/.claude/skills (every project)
./install.sh --profile skills --dry-run          # show what would happen
./install.sh --profile skills --force            # replace files the installer does not own
```

### What lands on disk

Five skills:

| Skill | Invoke | What it does |
|---|---|---|
| `generating-dataflow-pipeline` | `/generating-dataflow-pipeline` | Target + sample JSONL → operator chain → runnable pipeline |
| `dataflow-dev` | `/dataflow-dev` | Developer assistant: new operators/pipelines/prompts, diagnose errors, code review |
| `dataflow-operator-builder` | `/dataflow-operator-builder` | Scaffold an operator with registration, CLI wrapper and tests |
| `prompt-template-builder` | `/prompt-template-builder` | Build reusable `prompt_template` classes |
| `core_text` | *(not invoked)* | Per-operator API reference the pipeline skill reads |

### Per agent: where they go, and what "installed" means

`--scope` only affects Claude Code. Codex and Cursor are directory-scoped by
design — there is no global install for either, and `--scope user` does not
change that.

| Agent | Installed to | Available in | Slash commands | Verify |
|---|---|---|---|---|
| **Claude Code** | `./.claude/skills/` — or `~/.claude/skills/` with `--scope user` | this repo; every project with `--scope user` | yes | `/generating-dataflow-pipeline` appears in completion |
| **Codex** | `./AGENTS.md` (routing table) + `./.codex/skills/` (full text) | this repo only — Codex reads `AGENTS.md` from its start directory | no; ask in prose | open `AGENTS.md` and check the routing table |
| **Cursor** | `./.cursor/skills/` + `./.cursor/rules/` | this repo only, opened as a project in Cursor | no; rules auto-attach by file glob | rules listed under Settings → Rules |

Nothing else is written: no pip, no npm, no MCP configuration.

Note that `.claude/skills/` is generated, not tracked in git — `skills/canonical/`
is the only source. See [ADR-001](../architecture/adr-001-source-of-truth.md).

## Minimal verification

```bash
ls .claude/skills/generating-dataflow-pipeline/SKILL.md      # project scope
ls ~/.claude/skills/generating-dataflow-pipeline/SKILL.md     # --scope user
```

Then in Claude Code:

```
/generating-dataflow-pipeline
Target: Generate product descriptions and filter high-quality ones
Sample file: ./data/products.jsonl
Expected outputs: generated_description, quality_score
```

You should get an operator decision JSON followed by a complete pipeline `.py`. If the slash command does not appear in completion, restart the agent so it rescans the skills directory.

## Upgrade

```bash
git pull
./install.sh --profile skills --force
```

Without `--force`, anything the installer cannot prove it wrote is left alone,
and it says so. That covers three cases:

- a skill you wrote yourself that happens to share a name with one we ship
- a skill we installed that you have since edited
- a hand-written `AGENTS.md` or `.cursor/skills/<your-skill>/`

Its own unmodified output is refreshed silently, so ordinary upgrades are quiet.
`--force` replaces the managed entries; files that are not part of this repo's
skill set are never touched, with or without `--force`.

## Uninstall

```bash
./install.sh --uninstall
```

Removes only what an install actually created, recorded in
`.dataflow-install/receipt-<target-hash>`. Three safeguards:

- a skill that was **already present** when you installed is never recorded, so
  it is never removed — even if its contents matched what this repo ships
- a skill you **edited after** installing is detected by checksum and kept, with
  a warning telling you the path if you want it gone
- project-scope and user-scope installs get **separate receipts**, so
  uninstalling one cannot touch the other's skills

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| Slash command missing | Agent has not rescanned | Restart the agent |
| `SKILL.md missing` during install | Interrupted copy | Re-run with `--force` |
| Agent invents operators that don't exist | It isn't reading the skill | Confirm the skill is in the directory the agent actually reads; for Cursor that is `.cursor/skills/` |
| Agent uses a real operator with wrong params | Bundled reference is older than your DataFlow | Use the [`harness`](harness.md) profile, which queries the live registry |

## Relationship to OpenDCAI/DataFlow-Skills

These skills previously lived in a separate repo. This repo is now the single source of truth — see [ADR-001](../architecture/adr-001-source-of-truth.md) and the [migration note](../migration/from-dataflow-skills.md).

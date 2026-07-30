# Migrating from `scripts/setup_all.sh`

The old scripts still work — they forward to the new entry point and print a
deprecation notice. Two behaviours changed, and one of them is deliberate.

## Command mapping

| Old | New |
|---|---|
| `./scripts/setup_all.sh` | `./install.sh --profile webui` |
| `./scripts/setup_all.sh --check` | `./install.sh --profile webui --check` |
| `./scripts/setup_agent.sh claude` | `./install.sh configure-agent --agent claude` |
| `./scripts/setup_agent.sh cursor` | `./install.sh configure-agent --agent cursor` |
| `./scripts/setup_agent.sh codex` | `./install.sh configure-agent --agent codex --scope user` |
| `./scripts/setup_agent.sh --print-config <a>` | `./install.sh configure-agent --agent <a> --dry-run` |
| `./scripts/setup_agent.sh all` | *no equivalent — configure each agent you use* |

New capabilities with no old equivalent:

```bash
./install.sh --list                      # compare the three profiles
./install.sh --profile harness           # backend + MCP, no Node.js
./install.sh --profile skills            # skills only, installs no packages
./install.sh --profile webui --dry-run   # show every step, change nothing
./install.sh --uninstall                 # remove what an install recorded
```

## Change 1: installing no longer configures your agent

`setup_all.sh` ended by running `setup_agent.sh all`, which wrote
`~/.codex/config.toml` and `~/.cursor/mcp.json`. Installing now writes no agent
config at all. Run the configurator yourself:

```bash
./install.sh --profile webui
./install.sh configure-agent --agent claude
```

Reasoning in [ADR-003](../architecture/adr-003-install-configure-split.md).

## Change 2: `$HOME` needs explicit consent

Agent config defaults to **project scope**. To write user-level config:

```bash
./install.sh configure-agent --agent codex --scope user
```

It shows a diff and asks before writing. Add `--yes` to skip the prompt in a
script.

`setup_agent.sh all` is refused rather than silently mapped, because it wrote
three config files, two of them in `$HOME`, without asking.

## If the old script already modified your config

Nothing needs undoing. The new configurator is idempotent and merges: it will
report "no change" if your existing `dataflow` entry already matches.

Worth checking once, if you had other MCP servers configured before running the
old script — its Cursor path could overwrite `~/.cursor/mcp.json`:

```bash
cat ~/.cursor/mcp.json      # are your other servers still listed?
```

If something is missing, re-add it. The new merge path preserves other servers
and refuses to touch a file it cannot parse.

## `AGENTS.md` and `.cursor/rules/` are now generated

`setup_agent.sh` regenerated `AGENTS.md` and `.cursor/rules/dataflow-pipeline.mdc`.
Those are now produced from `skills/canonical/` by:

```bash
make skills      # = python3 installers/generate_agent_assets.py
```

They are also **no longer tracked in git**. `.claude/skills/`, `.cursor/skills/`,
`.codex/skills/`, `AGENTS.md` and the per-skill `.cursor/rules/*.mdc` are build
output now, so a fresh clone will not have them until you run the command above
(or `./install.sh`, which does it for you). If `git status` after pulling shows
those paths as untracked, that is correct.

`AGENTS.md` also changed shape: it used to inline every skill's full text (~1100
lines). It is now a routing table that points at `.codex/skills/<id>/SKILL.md`, so
an agent reads only the skill it needs.

Two renamed rules, because rule files now match skill ids:

| Old | New |
|---|---|
| `.cursor/rules/dataflow-pipeline.mdc` | `.cursor/rules/generating-dataflow-pipeline.mdc` |
| `.cursor/rules/dataflow-pipeline-generator.mdc` | *(merged into the above)* |

Both old files are deleted on regenerate. If you hand-edited either, your changes
are gone — move them into `skills/canonical/` and regenerate. CI fails on
hand-edited generated files.

Hand-written rules with no skill counterpart are untouched: `backend-api.mdc`,
`frontend-vue.mdc`, `dataflow-json-schema.mdc`, `webui-change-policy.mdc`.

## Removal timeline

The wrappers are kept for one or two minor releases, then removed. Update your
scripts and docs now.

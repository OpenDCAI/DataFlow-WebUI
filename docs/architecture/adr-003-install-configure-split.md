# ADR-003: Installing never writes agent configuration

- Status: accepted
- Date: 2026-07-29

## Context

`scripts/setup_all.sh` finished by calling `scripts/setup_agent.sh all`, which as
a side effect of "install this project":

- appended `[mcp_servers.dataflow]` to `~/.codex/config.toml`, creating the file
  if absent
- wrote `~/.cursor/mcp.json`, guarded only by a `grep` for the string
  `"dataflow"` — an existing user-level config with other MCP servers and no
  `dataflow` entry was overwritten wholesale
- regenerated `AGENTS.md` and `.cursor/rules/dataflow-pipeline.mdc` from the
  canonical skill

Two distinct problems. First, a user running an installer to get a local tool did
not ask for their home directory to be modified, and got no preview. Second, the
Cursor path could destroy unrelated configuration.

There was also no way to express "install the backend but leave my agent setup
alone", which the `harness` profile needs.

## Decision

Installing and configuring are separate commands.

```bash
./install.sh --profile harness                          # writes no agent config
./install.sh configure-agent --agent codex --scope user  # explicit, previewed
```

Rules for `configure-agent`:

1. **Default scope is `project`** — writes only inside the repo (`.mcp.json`,
   `.cursor/mcp.json`). `--scope user` is required to touch `$HOME`. Codex is the
   exception: it reads only `~/.codex/config.toml` and offers no flag to redirect
   it, so `--scope project` is *rejected* for Codex rather than writing a file
   that would be silently ignored.
2. **Diff before write, always.** For user scope, also a `y/N` prompt unless
   `--yes` is passed.
3. **Merge, never replace, and only when the file can be parsed.** Configs are
   parsed with a real parser before any edit — `json` for Claude/Cursor,
   `tomllib`/`tomli` for Codex. If no TOML parser is available, the command
   refuses and prints the block to add by hand rather than editing a file it
   cannot validate. Other servers and unmanaged keys inside the `dataflow` entry
   are preserved.
4. **Refuse conflicts instead of resolving them.** An existing `dataflow` entry
   pointing at a different URL, or configured as a `command`/stdio server rather
   than SSE, requires `--force`. Silently merging a URL into a stdio definition
   would produce a hybrid that is valid as neither.
5. **Never touch credentials.** No key is read, written or logged. Agents get
   credentials from the environment at run time.
6. **Idempotent.** Re-running reports "no change" instead of rewriting.

Each profile manifest declares a `must_not_touch` list. `install.sh` fingerprints
every one of those paths before running any step — for a directory, that is the
content hash of every file underneath — and compares afterwards, failing on any
addition, deletion or modification. The boundary is asserted, not just documented.

`./install.sh --profile <id>` also defaults to `--scope project`, so installing
writes inside the repo unless the user passes `--scope user`.

## Alternatives rejected

**Keep it automatic, add `--no-agent-config`.** Safe behaviour should not be
opt-in; the default is what most users get.

**Prompt during install.** A prompt in the middle of a long install is easy to
accept without reading, and it makes the installer non-scriptable.

**Only ever write project scope.** Codex genuinely reads `~/.codex/config.toml`,
so a user-scope path has to exist. The answer is consent and a diff, not removal.

## Consequences

Good:

- installing cannot surprise a user by editing `$HOME`
- an existing MCP config with other servers survives
- `harness` and `skills` profiles become expressible
- the boundary is enforced by an assertion in every install run

Costs:

- one extra command for users who did want everything configured. The installer's
  own "next steps" output names it
- `scripts/setup_agent.sh all` no longer works; it now explains why and lists the
  per-agent commands. See [the migration note](../migration/from-setup-scripts.md)

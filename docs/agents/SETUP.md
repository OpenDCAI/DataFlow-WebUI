# Agent setup instructions

You are an AI agent asked to set up DataFlow-Harness. This document is the
authoritative procedure. It states what you may do without asking, what you must
ask about first, and how to tell whether you succeeded.

A human can read this too, but it is written for you.

Skill content is **not** duplicated here. Once setup is done, the installed
skills tell you how to build pipelines.

## 1. Pick the profile before installing anything

Do not default to the largest install. Ask the user which they want if it is not
already clear from the conversation:

| Profile | Choose when | Cost |
|---|---|---|
| `skills` | They want you to write DataFlow code; no server needed | seconds, installs no packages |
| `harness` | They want you to query the live operator registry and run pipelines via MCP, no browser | ~1 min, pip only |
| `webui` | They want a visual DAG canvas in the browser | minutes, pip + npm |

If the user says only "set up DataFlow" and gives no other signal, ask. The three
differ by orders of magnitude in install cost and in what they change.

## 2. Inspect the plan before running it

```bash
./install.sh --list
./install.sh --profile <id> --check      # prerequisites; installs nothing
./install.sh --profile <id> --dry-run    # every step, verbatim; changes nothing
```

`--dry-run` output is the contract. If a step looks wrong, stop and tell the user
rather than running it.

## 3. Install

```bash
./install.sh --profile <id>
```

You are authorized to run this without further confirmation. It:

- installs Python/Node dependencies for **this project only** (per profile)
- writes inside this repo only, because `--scope project` is the default. With
  `--scope user` it also writes `~/.claude/skills`
- writes **no** agent MCP configuration, in either scope
- fingerprints every path the profile declared off-limits before and after, and
  fails if any of them changed

If a prerequisite is missing, the installer names it. Report exactly what the
user needs to install; do **not** install system packages or language runtimes
yourself.

## 4. Configure an agent — only if asked

This is deliberately separate from installing.

```bash
./install.sh configure-agent --agent claude                  # project scope (default)
./install.sh configure-agent --agent cursor --dry-run        # preview
./install.sh configure-agent --agent codex  --scope user     # writes $HOME — needs consent
```

Rules you must follow:

- Default to `--scope project`. It writes only inside this repo.
- `--scope user` modifies files in the user's home directory. **Ask first.** Show
  them the `--dry-run` diff before you do it.
- **Codex is the exception:** it reads only `~/.codex/config.toml` and has no flag
  to point elsewhere, so it has no project scope. `--scope user` is required, and
  the command refuses project scope rather than writing a file Codex ignores. Ask
  the user before configuring Codex.
- Never write API keys anywhere. Agents read credentials from environment
  variables at run time. If auth is missing, tell the user which variable to
  export — do not ask them to paste a key into the chat, and do not put one in a
  file.

## 5. Start the service (harness / webui only)

```bash
./scripts/start.sh --daemon
./scripts/start.sh --status
```

Note for the user: the service binds `0.0.0.0:8000` by default and has **no
authentication**. On an untrusted network, suggest `DATAFLOW_HOST=127.0.0.1`.

## 6. Verify, and report honestly

| Profile | Success criterion |
|---|---|
| `skills` | `ls .claude/skills/generating-dataflow-pipeline/SKILL.md` succeeds (or `~/.claude/skills/...` if you used `--scope user`) |
| `harness` | `curl -sf http://localhost:8000/api/v1/operators/categories` returns categories |
| `webui` | The above, plus `http://localhost:8000/` serves the canvas |

Then one real MCP call, for `harness` / `webui`:

```bash
claude --print --mcp-config .mcp.json --output-format text \
  "call mcp__dataflow__list_operator_categories and report the result"
```

If a step failed, say so and quote the error. Do not report success because the
command exited 0 while the verification did not actually run — `--dry-run` prints
`PLAN` lines and verifies nothing.

## 7. A fresh clone has no generated skill files

`.claude/skills/`, `.cursor/skills/`, `.cursor/rules/<skill>.mdc`, `.codex/skills/`
and `AGENTS.md` are generated from `skills/canonical/` and are **not** tracked in
git. On a fresh clone they do not exist. `./install.sh` generates them as part of installing, or
generate them alone with:

```bash
make skills      # = python3 installers/generate_agent_assets.py
```

If you are looking for skill instructions in a clone and the directory is missing,
that is expected — generate it, do not recreate it by hand.

## 8. Authorization boundaries

You **may**, without asking:

- run `./install.sh` with any read-only flag (`--list`, `--check`, `--dry-run`)
- run `make skills` to generate the agent assets
- run `./install.sh --profile <id>` once the user has chosen a profile
- run `./scripts/start.sh` and its `--status` / `--stop` forms
- run the checks in `installers/checks/`
- edit project-scoped config in this repo: `.mcp.json`, `.cursor/mcp.json`

You **must ask first** to:

- write anything in `$HOME` — including `--scope user`
- install an agent CLI, a language runtime, or any system package
- change `DATAFLOW_PORT` / `DATAFLOW_HOST` if something else may depend on it
- delete `backend/data/` or `frontend/dist/` — the former holds the user's pipelines
- run `./install.sh --uninstall`

You **must not**:

- write, log, echo or commit API keys
- edit unrelated files in `$HOME` (`.bashrc`, `.zshrc`, ssh config, …)
- touch other repositories, databases or cloud resources
- edit generated files by hand: `.claude/skills/`, `.cursor/skills/`,
  `.cursor/rules/<skill-id>.mdc`, `.codex/skills/`, `AGENTS.md`. These are
  untracked build output. Edit `skills/canonical/` and regenerate — CI fails on
  hand-edits.

## 9. When to stop and ask

- Prerequisites missing (no Python 3.10+, no Node 20+)
- An unusual auth setup (Azure OpenAI, a custom gateway)
- A previous config points at a different port than the one you are configuring
- A profile boundary assertion fails — that is an installer bug; report it, do
  not work around it
- Any step fails twice for the same reason

Pausing for one round trip is a better outcome than silently changing the user's
environment.

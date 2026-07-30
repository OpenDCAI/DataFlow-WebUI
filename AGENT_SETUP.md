# AGENT_SETUP.md

> **Moved.** The agent setup instructions now live at
> **[docs/agents/SETUP.md](docs/agents/SETUP.md)**.

This file is kept as a pointer because the root README and older instructions
told agents to read `AGENT_SETUP.md` first.

If you are an AI agent asked to set up this project, read
[docs/agents/SETUP.md](docs/agents/SETUP.md). It covers:

- choosing between the `webui`, `harness` and `skills` profiles before installing
  anything (they differ by orders of magnitude in cost and in what they change)
- inspecting the plan with `--check` and `--dry-run` before running it
- which actions you are authorized to take without asking, and which require
  the human's consent — notably anything that writes to their home directory
- success criteria for each profile, and how to report failures honestly

The one-command path, for reference:

```bash
./install.sh --list                            # compare the three profiles
./install.sh --profile <webui|harness|skills>   # install
./install.sh configure-agent --agent claude     # separate, explicit step
./scripts/start.sh --daemon                     # harness/webui only
```

Behaviour that changed from earlier versions of this document: installing no
longer configures your agent or writes to `$HOME`. See
[docs/migration/from-setup-scripts.md](docs/migration/from-setup-scripts.md).

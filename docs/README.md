# Documentation

## Choosing and installing a layer

| | |
|---|---|
| [profiles/webui.md](profiles/webui.md) | Full stack: canvas + backend + MCP |
| [profiles/harness.md](profiles/harness.md) | Backend + MCP, no Node.js |
| [profiles/skills.md](profiles/skills.md) | Agent skills only, installs no packages |

Not sure which? The [root README](../README.md) has a 30-second comparison, or run
`./install.sh --list`.

## For agents

| | |
|---|---|
| [agents/SETUP.md](agents/SETUP.md) | Setup procedure, authorization boundaries, success criteria |

## Architecture and decisions

| | |
|---|---|
| [architecture/overview.md](architecture/overview.md) | Component boundaries, config ownership, security posture, static guards |
| [architecture/adr-001-source-of-truth.md](architecture/adr-001-source-of-truth.md) | Why skills have one source and everything else is generated |
| [architecture/adr-002-package-managers.md](architecture/adr-002-package-managers.md) | npm vs Yarn, resolved — plus required follow-up |
| [architecture/adr-003-install-configure-split.md](architecture/adr-003-install-configure-split.md) | Why installing writes no agent config |
| [architecture/branch-audit.md](architecture/branch-audit.md) | Status and disposition of every remote branch |

## Migration

| | |
|---|---|
| [migration/from-setup-scripts.md](migration/from-setup-scripts.md) | From `scripts/setup_all.sh` / `setup_agent.sh` |
| [migration/from-dataflow-skills.md](migration/from-dataflow-skills.md) | From the `OpenDCAI/DataFlow-Skills` repo |

## Other

| | |
|---|---|
| [RELEASE-PACKAGE.md](RELEASE-PACKAGE.md) | Running a downloaded release zip (中文 / English) |
| [install-claude-code.md](install-claude-code.md) | Installing the Claude Code CLI |
| [install-claude-code_zh.md](install-claude-code_zh.md) | Claude Code CLI 安装指南 |
| [math_data_synthesis_system.md](math_data_synthesis_system.md) | Math data synthesis case study |

## Editing docs and skills

Skill content is edited **only** in `skills/canonical/`. The copies under
`.claude/skills/`, `.cursor/skills/`, `.cursor/rules/`, `.codex/skills/` and
`AGENTS.md` are generated and untracked:

```bash
python3 installers/generate_agent_assets.py           # regenerate
python3 installers/generate_agent_assets.py --check    # what CI enforces
```

Before pushing:

```bash
bash installers/checks/check_shell.sh
python3 installers/checks/check_skills.py
python3 installers/checks/check_profiles.py
python3 installers/checks/check_mcp_whitelist.py
```

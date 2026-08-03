# DataFlow-Harness

[![](https://img.shields.io/github/repo-size/OpenDCAI/DataFlow-WebUI?color=green)](https://github.com/OpenDCAI/DataFlow-WebUI)
[![Technical Report](https://img.shields.io/badge/Technical%20Report-arXiv%3A2607.16617-B31B1B?logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2607.16617)

中文文档：**[README_zh.md](README_zh.md)**

Build, run and manage [DataFlow](https://github.com/OpenDCAI/DataFlow) data pipelines with a coding agent — through a visual canvas, through MCP, or with skills alone.

## Names you will see

| Name | What it refers to |
|---|---|
| **DataFlow** | The upstream data-processing framework ([OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow)). Installed as the `open-dataflow` package. Not this repo. |
| **DataFlow-Harness** | The system this repo builds: skills + MCP + WebUI working together. The name of the product, and of the paper. |
| **DataFlow-WebUI** | The repository name, and the visual-canvas layer specifically. Kept for URL stability. |
| **`DataFlow-WebUI-<version>.zip`** | A release package with the frontend pre-built, for running without a clone. See [docs/RELEASE-PACKAGE.md](docs/RELEASE-PACKAGE.md). |

This repo ships **three independent layers**. Install only the one you need.
They are independent at install and runtime; internally, all agent variants are
rendered from the same `skills/canonical/` source so the standalone and
MCP-aware instructions cannot drift.

## Which layer do I want?

| | `webui` | `harness` | `skills` |
|---|---|---|---|
| **You get** | Visual DAG canvas + backend + MCP | Backend + MCP, no browser UI | Agent skills only |
| **You need** | Python 3.10+, Node 20+ | Python 3.10+ | Python 3.9+ (to render the skills) |
| **Installs packages** | yes (pip + npm) | yes (pip) | **no** |
| **Runs a server** | yes, port 8000 | yes, port 8000 | **no** |
| **Agent writes pipelines** | ✅ | ✅ | ✅ |
| **Agent sees live operator registry** | ✅ | ✅ | ✗ (uses bundled reference) |
| **Pipelines appear on a canvas** | ✅ | ✗ | ✗ |
| **Install time** | minutes | ~1 min | seconds |

The `skills` profile installs no packages, but it does run a Python script to
render the skill files, so Python 3.9+ must be present.

**30-second decision:**

- You want to *see and edit* pipelines as a graph → **`webui`**
- You drive everything from Claude Code / Codex / Cursor and never open a browser → **`harness`**
- You just want your agent to write correct DataFlow code, with no server → **`skills`**

```bash
git clone https://github.com/OpenDCAI/DataFlow-WebUI.git
cd DataFlow-WebUI

./install.sh --list                  # compare the three, in detail
./install.sh --profile skills        # or harness, or webui
```

Every profile supports `--check` (prerequisites only), `--dry-run` (show the plan, change nothing) and `--uninstall`.

Full per-layer guides: **[webui](docs/profiles/webui.md)** · **[harness](docs/profiles/harness.md)** · **[skills](docs/profiles/skills.md)**

## Installing never writes agent configuration

Installing and configuring an agent are two separate commands, on purpose:

```bash
./install.sh --profile harness                      # installs; writes no agent config
./install.sh configure-agent --agent claude         # project-scoped, shows a diff first
./install.sh configure-agent --agent codex --scope user   # asks before writing ~/.codex/
```

Installing **never writes MCP configuration**, in either scope. That is
`configure-agent`'s job.

### Where the skills land, per agent

`--scope` only affects Claude Code. The other two agents read from the repo, so
their assets are always installed here:

| Agent | Installed to | Available in | Verify |
|---|---|---|---|
| **Claude Code** | `./.claude/skills/` (default), or `~/.claude/skills/` with `--scope user` | this repo, or every project with `--scope user` | `/generating-dataflow-pipeline` appears in completion |
| **Codex** | `./AGENTS.md` + `./.codex/skills/` in this repo | this repo only — Codex reads `AGENTS.md` from the directory it starts in | open `AGENTS.md`; it routes to `.codex/skills/` |
| **Cursor** | `./.cursor/skills/` and `./.cursor/rules/` in this repo | this repo only, when opened as a project in Cursor | rules appear under Settings → Rules |

There is no global install for Codex or Cursor — both are directory-scoped by
design. `--scope user` does not change that.

Each profile declares the paths it must not touch, and the installer fingerprints
them before and after the install and fails if any changed. Anything it cannot
prove it wrote is never overwritten without `--force`.

Existing MCP servers in your config are merged, never overwritten. No API keys are read, written or logged.

Upgrading from `scripts/setup_all.sh`? See [docs/migration/from-setup-scripts.md](docs/migration/from-setup-scripts.md).

## What DataFlow-Harness is

DataFlow-Harness combines **skills** (procedural knowledge about operator selection, schema links and assembly order), **MCP** (a live connection to the operator registry and current pipeline state), and the **WebUI** (turning agent-built workflows into persistent, editable DAGs).

<p align="center">
  <img src="https://github.com/user-attachments/assets/c54d92ea-a6d5-4c3c-8144-87c3cdfee276" alt="DataFlow-WebUI" width="90%">
</p>

*The dual-modality interface: conversational agent and visual DAG editor stay in sync.*

<p align="center">
  <img width="1280" height="638" alt="DataFlow-Harness architecture" src="https://github.com/user-attachments/assets/d9c862ac-a1a2-42b1-9f07-440d20d59d8f" />
</p>

*A shared pipeline representation synchronized across the agent runtime and the WebUI. Skills guide construction; the validation engine checks DAG structure and schema compatibility.*

### Why it helps

**Bridges the NL2Pipeline gap.** Natural-language intent becomes a persistent, platform-native pipeline artifact you can inspect, edit, run and reuse.

**Procedural knowledge, not just tool lists.** Building a VQA dataset from textbooks needs PDF parsing, layout understanding, OCR, image-text alignment, QA extraction and quality filtering *in the right order*. That ordering knowledge is what the skills encode.

**Reusable workflows.** Data preparation becomes reusable pipelines rather than one-off scripts.

**Reported results.** The DataFlow-Harness paper reports a 93.3% end-to-end pass
rate on a 12-task data-engineering benchmark, with 72.5% lower cost and 49.9%
lower generation latency than vanilla Claude Code.

Those figures come from the paper's own harness and are **not reproducible from
this repository** — the benchmark tasks, run configuration and raw results are not
included here. Treat them as published findings, not as a claim you can verify by
installing this repo. Details and methodology: [DataFlow-Harness](https://huggingface.co/papers/2607.16617).

## Supported agents

| Agent | Mode | MCP config | Auth |
|---|---|---|---|
| **Claude Code** | WebUI-dispatched, or in your terminal | `.mcp.json` (project) | `ANTHROPIC_API_KEY`, or `ANTHROPIC_BASE_URL` for a gateway |
| **Codex** | WebUI-dispatched, or in your terminal | `~/.codex/config.toml` | `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL`), or `codex login` OAuth |
| **Cursor** | IDE only — not dispatched by the WebUI | `.cursor/mcp.json` (project) | Cursor built-in |

Cursor is used by opening this project in the IDE; its agent discovers the MCP server and pushes pipelines onto the canvas. It is not driven from the WebUI chat panel.

## For agents setting this up

If you are an AI agent configuring this repo, read **[docs/agents/SETUP.md](docs/agents/SETUP.md)**. It states the authorization boundaries, the exact commands to run, success criteria, and which actions require asking the human first.

## Architecture and decisions

- [Component boundaries](docs/architecture/overview.md) — how the three layers depend on each other
- [ADR-001: single source of truth](docs/architecture/adr-001-source-of-truth.md) — why skills live in one repo
- [ADR-002: one package manager](docs/architecture/adr-002-package-managers.md) — npm vs Yarn, resolved
- [ADR-003: install/configure split](docs/architecture/adr-003-install-configure-split.md) — why installing writes no agent config
- [Branch audit](docs/architecture/branch-audit.md) — status of every remote branch

## Contributing

Skills are edited in `skills/canonical/` only. The files under `.claude/skills/`,
`.cursor/skills/`, `.cursor/rules/<skill>.mdc`, `.codex/skills/` and `AGENTS.md`
are generated build output and are **not tracked in git** — a fresh clone will not
have them:

```bash
make skills      # generate agent assets from skills/canonical/
make check       # run every static check CI runs
```

CI regenerates and diffs, so a hand-edited generated file fails the build.

## Citation

```bibtex
@article{liang2025dataflow,
  title={DataFlow: An LLM-Driven Framework for Unified Data Preparation and Workflow Automation in the Era of Data-Centric AI},
  author={Liang, Hao and Ma, Xiaochen and Liu, Zhou and Wong, Zhen Hao and Zhao, Zhengyang and Meng, Zimo and He, Runming and Shen, Chengyu and Cai, Qifeng and Han, Zhaoyang and others},
  journal={arXiv preprint arXiv:2512.16676},
  year={2025}
}
```


## Community

<p align="center">
  <img src="https://github.com/user-attachments/assets/b958dc89-d76e-4e47-9277-22b3f6661944" alt="DataFlow community QR code" width="85%">
</p>

Licensed under Apache 2.0 — see [LICENSE](LICENSE).

# DataFlow-WebUI

[![](https://img.shields.io/github/repo-size/OpenDCAI/DataFlow-webui?color=green)](https://github.com/OpenDCAI/DataFlow-webui)

## Overview

**DataFlow-WebUI** is a full-stack open-source graphical interface for [DataFlow](https://github.com/OpenDCAI/DataFlow). It helps users build, run, and manage DataFlow pipelines through both a visual canvas and natural language interaction **with Code Agents such as Claude Code, Codex, and Cursor**.

DataFlow-WebUI is the engineering and interaction layer of [**DataFlow-Harness**](https://huggingface.co/papers/2607.16617). DataFlow-Harness brings together [**DataFlow-Skills**](https://github.com/OpenDCAI/DataFlow-Skills), **MCP**, and **DataFlow-WebUI**. DataFlow-Skills provide workflow knowledge such as operator selection, schema links, and assembly steps. MCP connects Agents to the live operator registry and current pipeline state. DataFlow-WebUI turns Agent-built workflows into persistent, editable visual DAGs for AI-ready data preparation, including LLM fine-tuning and RAG knowledge base building.

<p align="center">
  <img src="https://github.com/user-attachments/assets/c54d92ea-a6d5-4c3c-8144-87c3cdfee276" alt="DataFlow-WebUI" width="90%">
</p>

*The dual-modality interface of DataFlow-WebUI, illustrating the synchronization between the conversational Agent and the visual DAG editor.*

<p align="center">
  <img width="1280" height="638" alt="1280X1280 (1)" src="https://github.com/user-attachments/assets/d9c862ac-a1a2-42b1-9f07-440d20d59d8f" />
</p>

*The DataFlow-Harness architecture. A shared pipeline representation is synchronized across the Agent runtime and DataFlow-WebUI. DataFlow-Skills guide construction, while the Validation Engine checks DAG structure and schema compatibility.*


---
## Key Features

### ✅ Bridges the NL2Pipeline gap

DataFlow-WebUI helps turn natural-language workflow intent into persistent, platform-native pipeline artifacts. Users can inspect, edit, run, and reuse the generated workflows in the visual DAG canvas.

### 🧠 Procedural knowledge for complex data workflows

Many data tasks require more than knowing which tools are available. They also require knowing how to use these tools in the right order. For example, building a VQA dataset from textbooks may involve PDF parsing, layout understanding, OCR, image-text alignment, QA extraction, and quality filtering. DataFlow-WebUI provides this procedural knowledge to Code Agents, helping them build better workflows for complex tasks.

### ⚙️ Better for long-term data workflow reuse

DataFlow-WebUI makes data workflows visible, editable, runnable, and reusable. For teams working on LLM training, RAG, or data evaluation, this helps turn data preparation from one-time scripts into reusable DataFlow pipelines.

### 📊 DataFlow-Harness powered data preparation

In the DataFlow-Harness evaluation, the system reaches a 93.3% observed end-to-end pass rate on a 12-task data engineering benchmark. Compared with Vanilla Claude Code, it reduces measured cost by 72.5% and generation latency by 49.9%. This shows the efficiency of the Harness design used by DataFlow-WebUI.

---

## Quick Start

### Option A: Let your AI agent set it up (recommended)

If you already have **Claude Code**, **Codex**, or **Cursor** installed, just
open this project and tell your agent:

> 请阅读 AGENT_SETUP.md 并帮我完成所有配置

The agent will run `./scripts/setup_all.sh`, configure MCP, and get everything
ready. You only need **Python 3.10+** and **Node.js 20+** pre-installed.

### Option B: One-command manual setup

```shell
git clone https://github.com/OpenDCAI/DataFlow-WebUI.git
cd DataFlow-WebUI
./scripts/setup_all.sh
./scripts/start.sh
```

`setup_all.sh` handles everything: checks prerequisites, installs DataFlow +
backend deps + frontend build, and configures agent MCP connections. It's
idempotent — safe to re-run.

---

## Prerequisites

* **Python 3.10+** with pip
* **Node.js 20+** with npm (recommend [nvm](https://github.com/nvm-sh/nvm))
* **Git**
* At least one code agent CLI:
  - **Claude Code:** `curl -fsSL https://claude.ai/code/install.sh | sh`
  - **Codex:** `npm i -g @openai/codex`
  - **Cursor:** [Download Cursor IDE](https://cursor.com)

---

## Choose Your Code Agent

DataFlow-WebUI supports multiple code agents in two usage modes:

### WebUI Chat Agents (dispatched from the browser)

These agents are spawned headlessly by the WebUI backend when you chat in the
browser. Pick one from the dropdown next to the chat title.

| Agent | CLI binary | MCP config location | Auth |
|---|---|---|---|
| **Claude Code** | `claude` | `--mcp-config .mcp.json` (passed by backend) | `ANTHROPIC_API_KEY` (or `ANTHROPIC_BASE_URL` for 中转/gateway) |
| **Codex** | `codex` | `~/.codex/config.toml` `[mcp_servers.dataflow]` | `OPENAI_API_KEY` + optional `OPENAI_BASE_URL`，**或** `codex login` OAuth（ChatGPT Plus，无需 API key） |

### IDE / Terminal Agents (user-driven)

These agents run in your own IDE or terminal and connect to the WebUI's MCP
server to push pipelines onto the canvas.

| Agent | How to use | MCP config location | Auth |
|---|---|---|---|
| **Cursor IDE** | Open this project in Cursor; the Agent panel auto-discovers MCP | `.cursor/mcp.json` (project-scoped) | Cursor 内置认证 |
| **Claude Code (terminal)** | Run `claude` in this repo; it reads `.mcp.json` automatically | `.mcp.json` at repo root | `ANTHROPIC_API_KEY` |

> **Cursor 不通过 WebUI 前端调度。** 它的使用方式是在 Cursor IDE 中打开本项目，
> Agent 会自动发现 MCP server，可以直接创建/执行 pipeline 并同步到 WebUI 画布。

### Authentication setup

```shell
# Claude Code
export ANTHROPIC_API_KEY=sk-ant-...
# 如使用中转:
export ANTHROPIC_BASE_URL=https://your-gateway/v1

# Codex — 方式一: API key
export OPENAI_API_KEY=sk-...
# 如使用中转:
export OPENAI_BASE_URL=https://your-gateway/v1

# Codex — 方式二: ChatGPT Plus OAuth (无需 API key)
codex login
```

---

## Running the Project

```shell
# If you used setup_all.sh, just:
./scripts/start.sh

# Or manually:
cd backend && uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

---

## Access the Web UI

Once the backend is running, open your browser and visit:

```
http://localhost:8000/
```

> 💡 If you changed the backend port, replace `8000` with your custom port.

In the chat panel header you'll see a small **agent dropdown** — pick
Claude Code or Codex per session. Switching the dropdown starts a fresh
conversation (different agents do not share session ids). Your last choice
is remembered across reloads.

> 💡 如果你使用 Cursor IDE，无需在 WebUI 中选择 agent — 直接在 Cursor 的
> Agent 面板中对话即可，pipeline 会通过 MCP 同步到 WebUI 画布。

---

## Troubleshooting

| Symptom | Most likely cause | Fix |
|---|---|---|
| `<cli>: command not found` in backend logs | CLI binary is not on the same PATH the backend sees | Re-install or set `DATAFLOW_<KIND>_CLI=/abs/path/to/cli` before launching the backend |
| Chat replies are empty / immediate `done` | Agent failed to authenticate | Confirm the relevant API key is exported in the shell that started the backend; for Codex without API key, run `codex login` first |
| Tool calls fail with `MCP server not reachable` | The agent's MCP config doesn't point at this backend | Re-run `./scripts/setup_agent.sh <kind>` |
| Agent invents non-existent operators | Construction skill not loaded | For Cursor, re-run `./scripts/setup_agent.sh cursor` to regenerate `.cursor/rules/`; for Codex, regenerate `AGENTS.md` |
| `lang="zh"` produces 0 records on English data | Construction skill missing or stale | Same fix as above — the skill encodes the language-detection policy |
| Cursor IDE 中看不到 MCP 工具 | `.cursor/mcp.json` 缺失或 WebUI 后端未启动 | 运行 `./scripts/setup_agent.sh cursor` 并确保后端在 `localhost:8000` 运行 |

---

## 🎉 You’re All Set!

You should now have the full DataFlow-WebUI stack running locally. If you encounter issues, double-check your Node.js and Python versions, and feel free to open an issue on GitHub.

Happy hacking! 🚀


## Citation

If you use DataFlow in your research, feel free to give us a cite.

```bibtex
@article{liang2025dataflow,
  title={DataFlow: An LLM-Driven Framework for Unified Data Preparation and Workflow Automation in the Era of Data-Centric AI},
  author={Liang, Hao and Ma, Xiaochen and Liu, Zhou and Wong, Zhen Hao and Zhao, Zhengyang and Meng, Zimo and He, Runming and Shen, Chengyu and Cai, Qifeng and Han, Zhaoyang and others},
  journal={arXiv preprint arXiv:2512.16676},
  year={2025}
}
```

---

## Community & Support

Join the DataFlow community to get updates, ask questions, and share your feedback with the team.

Scan the QR code below to connect with us and follow the latest DataFlow-Harness progress.

<p align="center">
  <img src="https://github.com/user-attachments/assets/7992ab37-d5b1-4539-99e7-44139ca6808d" alt="DataFlow community QR code" width="85%">
</p>

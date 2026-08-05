# DataFlow-Harness

English: **[README.md](README.md)**

用 Coding Agent 构建、运行和管理 [DataFlow](https://github.com/OpenDCAI/DataFlow) 数据管线 —— 可以通过可视化画布、通过 MCP，或只用 skills。

## 名称说明

| 名称 | 指什么 |
|---|---|
| **DataFlow** | 上游数据处理框架（[OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow)），以 `open-dataflow` 包安装。不是本仓库。 |
| **DataFlow-Harness** | 本仓库构建的系统：skills + MCP + WebUI 的整体。产品名，也是论文名。 |
| **DataFlow-WebUI** | 仓库名，同时特指可视化画布这一层。为保持链接稳定而沿用。 |
| **`DataFlow-WebUI-<版本>.zip`** | 预构建前端的发布包，无需 clone 即可运行。见 [docs/RELEASE-PACKAGE.md](docs/RELEASE-PACKAGE.md)。 |

本仓库提供**三个相互独立的层**，按需安装其中一个即可。
这里的“独立”指安装和运行边界；内部的 standalone 与 MCP-aware Agent 指令
统一从 `skills/canonical/` 渲染，避免出现两套需要分别维护的内容。

## 我该装哪一层？

| | `webui` | `harness` | `skills` |
|---|---|---|---|
| **得到什么** | 可视化 DAG 画布 + 后端 + MCP | 后端 + MCP，无浏览器界面 | 仅 Agent skills |
| **需要什么** | Python 3.10+、Node 20+ | Python 3.10+ | Python 3.9+（仅用于生成技能文件） |
| **是否装包** | 是（uv + npm） | 是（uv） | **否** |
| **是否起服务** | 是，端口 8000 | 是，端口 8000 | **否** |
| **Agent 能写管线** | ✅ | ✅ | ✅ |
| **Agent 能查实时算子注册表** | ✅ | ✅ | ✗（用内置静态参考） |
| **管线出现在画布上** | ✅ | ✗ | ✗ |
| **安装耗时** | 几分钟 | 约 1 分钟 | 几秒 |

`skills` 层不安装任何包，但需要运行一个 Python 脚本来生成技能文件，因此要求本机有 Python 3.9+。

**30 秒决策：**

- 想把管线当成图来**看和改** → **`webui`**
- 全程在 Claude Code / Codex / Cursor 里操作，不开浏览器 → **`harness`**
- 只想让 Agent 写出正确的 DataFlow 代码，不起服务 → **`skills`**

```bash
git clone https://github.com/OpenDCAI/DataFlow-WebUI.git
cd DataFlow-WebUI

./install.sh --list                  # 详细对比三层
./install.sh --profile skills        # 或 harness、webui
```

三个 profile 都支持 `--check`（只查前置条件）、`--dry-run`（只打印计划，不改动任何文件）和 `--uninstall`。

分层详细文档：**[webui](docs/profiles/webui.md)** · **[harness](docs/profiles/harness.md)** · **[skills](docs/profiles/skills.md)**

## 安装与使用

`webui` profile 会安装完整的浏览器端栈。以下命令都在仓库根目录执行，
安装和启动应使用同一个已激活的环境。Python 推荐 3.10，最低要求也是
3.10；另外需要 Node.js 20+、npm、Git 和 uv。

各系统推荐安装方式：

| 系统 | Python / Git | Node.js 20+ / npm | uv |
|---|---|---|---|
| macOS | `brew install python@3.10 git` | nvm，然后 `nvm install 20` | `brew install uv` |
| Ubuntu/Debian | `sudo apt update && sudo apt install -y python3.10 python3.10-venv git` | [nvm](https://github.com/nvm-sh/nvm)，然后 `nvm install 20` | [uv 安装器](https://docs.astral.sh/uv/getting-started/installation/) |
| Windows PowerShell | `winget install Python.Python.3.10 Git.Git` | `winget install OpenJS.NodeJS.LTS` | [PowerShell 安装器](https://docs.astral.sh/uv/getting-started/installation/) |

macOS/Linux 可执行 `curl -LsSf https://astral.sh/uv/install.sh | sh` 安装 uv；
Windows PowerShell 可执行 `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`。
安装后重启终端，并确认 `python --version`、`node --version`（20+）、
`npm --version` 和 `uv --version` 可用。

二选一创建 Python 环境：

```bash
# venv（Windows PowerShell：py -3.10 -m venv .venv，然后 .venv\Scripts\Activate.ps1）
python3.10 -m venv .venv
source .venv/bin/activate

# 或 conda（所有系统）
conda create -n dataflow python=3.10 -y
conda activate dataflow
```

然后安装并启动：

```bash
./install.sh --profile webui
./scripts/start.sh             # 或 ./scripts/start.sh --daemon
```

浏览器打开 <http://localhost:8000/>，在聊天面板选择 Agent，描述想要的
数据管线并在画布中检查结果。uv 是默认 Python 包管理器；若必须使用 pip，
执行 `./install.sh --profile webui --pip`。

## 安装不会写入 Agent 配置

安装和配置 Agent 是两条独立命令，这是刻意设计：

```bash
./install.sh --profile harness                            # 安装；不写任何 agent 配置
./install.sh configure-agent --agent claude               # 项目级，写入前先显示 diff
./install.sh configure-agent --agent codex --scope user   # 写 ~/.codex/ 前会先询问
```

安装**在任何 scope 下都不会写 MCP 配置**，那是 `configure-agent` 的职责。

### 技能装到哪里（按 Agent 区分）

`--scope` 只影响 Claude Code。另外两个 Agent 从仓库目录读取，因此资产始终装在仓库内：

| Agent | 安装位置 | 生效范围 | 验证方式 |
|---|---|---|---|
| **Claude Code** | `./.claude/skills/`（默认），或 `--scope user` 时 `~/.claude/skills/` | 本仓库；`--scope user` 时所有项目 | 补全里出现 `/generating-dataflow-pipeline` |
| **Codex** | 仓库内 `./AGENTS.md` + `./.codex/skills/` | 仅本仓库 —— Codex 读取启动目录下的 `AGENTS.md` | 打开 `AGENTS.md`，查看指向 `.codex/skills/` 的路由表 |
| **Cursor** | 仓库内 `./.cursor/skills/` 与 `./.cursor/rules/` | 仅本仓库，且需在 Cursor 中作为项目打开 | Settings → Rules 中可见 |

Codex 和 Cursor 没有全局安装方式，二者按目录生效，`--scope user` 不改变这一点。

每个 profile 都声明了自己不得修改的路径；安装器在前后对这些路径做内容指纹比对，一旦改变即失败。任何无法证明由安装器写入的文件，都不会在没有 `--force` 的情况下被覆盖。

已有 MCP server 会被合并而非覆盖；安装器不会读取、写入或记录 API key。

从旧的 `scripts/setup_all.sh` 升级？见 [docs/migration/from-setup-scripts.md](docs/migration/from-setup-scripts.md)。

## DataFlow-Harness 是什么

DataFlow-Harness 把三部分组合起来：**skills**（算子选择、字段衔接、装配顺序等流程性知识）、**MCP**（连接 Agent 与实时算子注册表和当前管线状态）、**WebUI**（把 Agent 构建的工作流变成可持久化、可编辑的 DAG）。

论文中报告：在 12 项数据工程基准上端到端通过率 93.3%，相比原生 Claude Code 成本降低 72.5%、生成延迟降低 49.9%。

这些数字来自论文自有的评测框架，**无法从本仓库复现** —— 基准任务、运行配置和原始结果均未包含在此。请将其视为已发表的结论，而非安装本仓库即可验证的指标。方法细节见 [DataFlow-Harness 论文](https://huggingface.co/papers/2607.16617)。

## 支持的 Agent

| Agent | 使用方式 | MCP 配置位置 | 认证 |
|---|---|---|---|
| **Claude Code** | WebUI 调度，或在终端直接使用 | `.mcp.json`（项目级） | `ANTHROPIC_API_KEY`，或用 `ANTHROPIC_BASE_URL` 走中转 |
| **Codex** | WebUI 调度，或在终端直接使用 | `~/.codex/config.toml` | `OPENAI_API_KEY`（可配 `OPENAI_BASE_URL`），或 `codex login` OAuth |
| **Cursor** | 仅 IDE 模式 —— 不由 WebUI 调度 | `.cursor/mcp.json`（项目级） | Cursor 内置认证 |

Cursor 的用法是在 IDE 中打开本项目，其 Agent 会自动发现 MCP server 并把管线推送到画布，不通过 WebUI 聊天面板调度。

## 给 Agent 看的安装说明

如果你是正在配置本仓库的 AI Agent，请阅读 **[docs/agents/SETUP.md](docs/agents/SETUP.md)**：其中说明了授权边界、可执行的具体命令、成功判据，以及哪些操作必须先询问用户。

## 架构与决策记录

- [组件边界](docs/architecture/overview.md) —— 三层之间的依赖关系
- [ADR-001：唯一真源](docs/architecture/adr-001-source-of-truth.md) —— 技能为何只有一个源
- [ADR-002：统一包管理器](docs/architecture/adr-002-package-managers.md) —— npm 与 Yarn 的取舍
- [ADR-003：安装与配置分离](docs/architecture/adr-003-install-configure-split.md) —— 安装为何不写 agent 配置
- [分支审计](docs/architecture/branch-audit.md) —— 每个远端分支的处置状态

## 贡献

技能只在 `skills/canonical/` 中编辑。`.claude/skills/`、`.cursor/skills/`、`.cursor/rules/<skill>.mdc`、`.codex/skills/` 和 `AGENTS.md` 都是生成产物，**不纳入 git** —— 新 clone 不会带这些文件：

```bash
make skills      # 从 skills/canonical/ 生成 agent 资产
make check       # 运行 CI 的全部静态检查
```

CI 会重新生成并比对，手工修改生成文件会导致构建失败。

## 引用

```bibtex
@article{liang2025dataflow,
  title={DataFlow: An LLM-Driven Framework for Unified Data Preparation and Workflow Automation in the Era of Data-Centric AI},
  author={Liang, Hao and Ma, Xiaochen and Liu, Zhou and Wong, Zhen Hao and Zhao, Zhengyang and Meng, Zimo and He, Runming and Shen, Chengyu and Cai, Qifeng and Han, Zhaoyang and others},
  journal={arXiv preprint arXiv:2512.16676},
  year={2025}
}
```

采用 Apache 2.0 许可 —— 见 [LICENSE](LICENSE)。

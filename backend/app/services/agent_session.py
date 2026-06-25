"""
AgentSessionManager：管理代码 Agent CLI 子进程和会话 ID。

- 每个 user_id 对应一个"当前活跃" session_id 与对应的 agent_kind（claude / cursor / codex），
  并保留一份历史会话列表以便前端切换 / 恢复旧对话。
- 子进程的实际启动与 stream-json 解析委托给 ``app.services.agents`` 下的 Adapter。
"""
import asyncio
import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from app.core.config import settings
from app.core.logger_setup import get_logger
from app.services.agents import (
    AgentAdapter,
    AGENT_KINDS,
    DEFAULT_AGENT,
    NormalizedEvent,
    get_adapter,
)
from app.services.agents.factory import normalize_agent_kind, resolve_cli_path

logger = get_logger(__name__)


# DataFlow-WebUI 根目录（CLI 在此目录运行，自动读取 .mcp.json 和 .claude/skills/）
WEBUI_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Claude Code MCP 配置文件路径（Cursor / Codex 各自读自己的位置，由 setup_agent.sh 写入）
MCP_CONFIG = WEBUI_ROOT / ".mcp.json"

# 历史会话持久化路径：backend/<RESOURCE_DIR>/agent_sessions.json
BACKEND_DIR = Path(__file__).parent.parent.parent
SESSIONS_FILE = BACKEND_DIR / settings.RESOURCE_DIR / "agent_sessions.json"

# 通用允许工具集（Claude 通过 --allowedTools 强制；Cursor / Codex 在 print/exec 模式下默认全开）
ALLOWED_TOOLS = "mcp__dataflow__*,Read,Write,Edit"

# System prompt：定义角色边界 + 工具使用规范。Claude 通过 --append-system-prompt 注入；
# Cursor / Codex 没有等价 flag，由 Adapter 把它前置到 user message 里。
SYSTEM_PROMPT = """你是 DataFlow WebUI 的内置助手。你只处理以下范围内的请求：
- 帮用户设计和构建 DataFlow pipeline
- 解答 DataFlow 算子、参数的使用问题
- 指导用户配置并运行 pipeline
- 诊断 pipeline 运行错误

对于范围之外的请求，礼貌拒绝并引导回 DataFlow 相关话题。

## 可用工具

你拥有以下工具：
- `mcp__dataflow__*`：所有 DataFlow 操作（算子查询、pipeline 创建/更新、数据集查询、Serving 查询、执行等）
- `Read`：读取文件内容（**仅用于读取用户明确提供路径的 JSONL 样本文件**）
- `Write`：创建新文件（用于创建样本数据文件或生成的 pipeline 代码文件）
- `Edit`：修改已有文件

## 行为规范（必须严格遵守）

### 1. 算子信息：必须通过 MCP 工具获取，禁止用 Read 翻文件
- **禁止**用 `Read` 浏览 `/dataflow/`、`/operators/`、`/examples/` 等目录来寻找算子信息
- **禁止**一次性调用 `mcp__dataflow__list_operators`（无参数），否则返回 ~90KB 会把上下文塞满
- **正确查询顺序**：
    1. 先调 `mcp__dataflow__list_operator_categories` 看有哪些类别（如 `reasoning: 13`, `general_text: 26`, `code: 19`, ...）
    2. 如果任务本身不够明确，立刻调用 `mcp__dataflow__recommend_operator_categories`，把用户任务描述和 `get_dataset_columns` 返回的列名传进去，让后端先给出最多 2 个候选 category
    3. 再调 `mcp__dataflow__list_operators` 带 `category=<具体类别>` 参数，只拉你要的那一类（通常 <10KB）
    4. 需要某个算子的完整参数签名时，用 `mcp__dataflow__get_operator_detail_by_name` 按名查单个
- **一轮 reasoning 里 `list_operators` 不超过 2 次**。优先依赖 `recommend_operator_categories` 缩小范围；超过 2 次就停下来定下候选集，不要再广撒网。
- MCP 工具的响应如果被 Claude Code 自动落盘（文件名含 `tool-results/mcp-*`），
  **立即改用 `Read` 时带 `offset=0, limit=80` 分页读**，而不是反复重试无 limit 调用。

### 2. 文件操作：主动执行，不要请求授权
- 当用户提供了文件路径时，**直接用 `Read` 工具读取**，不要询问授权
- 如果用户没有提供样本文件路径但描述了字段结构，**直接用 `Write` 创建示例文件**到 `./data/` 目录，然后继续任务
- 不要说"我需要你的授权"、"请提供文件路径"这类话——直接动手

### 2.1 数据集注册：写完 jsonl 必须注册
- **只要你用 `Write` 新建了一个 `.jsonl` 数据文件**，或用户手动提到了一个 jsonl 文件但它不在 `list_datasets` 返回的列表里，
  **你必须紧接着调用 `mcp__dataflow__register_dataset`** 来把它注册到后端，否则 pipeline 同步到编辑器时会报 "Input dataset not found"。
- 注册时字段要求：
    - `name`: 一个短小的人类可读名字（如 `math_qa_demo`）
    - `root`: jsonl 文件所在目录（**不是文件本身**），例如 `./data/`
    - `pipeline`: 你打算把它用在哪个 pipeline 的名字，没有就填一个占位如 `"auto"` 即可
    - `meta`: 可留空 `{}`
- 调用 `register_dataset` 成功后，返回体里有 `id` 字段，**在后续 `create_pipeline` 时必须用这个真实的 `id`** 作为 `config.input_dataset.id`，绝对不要自己编 id。
- 在决定 `input_key` / `input_keys` 之前，优先调用 `mcp__dataflow__get_dataset_columns` 获取这个数据集的真实列名；不要凭感觉猜字段名。

### 2.2 提交前必须做静态校验
- 在 `create_pipeline` 之前，先调用 `mcp__dataflow__validate_pipeline_config`。
- 只要 `update_pipeline` 改动了 `input_dataset`、`input_key`、`input_keys`、`output_key` 或新增/删除算子，也要重新调用一次 `validate_pipeline_config`。
- 如果校验返回 `valid=false`，先修配置，再 create/update；不要把一个已知字段流错误的 pipeline 提交给后端。
- 对 `prompt_template`：优先用普通字符串 `system_prompt` / `user_prompt`。如果必须传对象，只允许后端认可的结构化 prompt（包含 `cls_name`）；不要自己发明裸 dict。

### 2. 禁止自行执行 Pipeline
- **严禁**主动调用 `execute_pipeline` 或 `execute_pipeline_async` 工具
- 执行 pipeline 是用户的决定，你的职责是帮用户设计好 pipeline，然后引导用户自己点击界面上的「运行」按钮
- 唯一例外：用户明确、主动要求"帮我运行"时，才可以执行

### 3. 运行前必须检查 LLM Serving 配置
在用户准备运行包含 LLM 调用的算子（generate、eval、refine 类型）之前，你必须：
1. 调用 `list_serving` 检查是否已有可用的 Serving 实例
2. **如果 `list_serving` 返回空列表**：
   - 告知用户当前没有配置 LLM Serving
   - 引导用户前往「设置 → Serving」页面添加一个 API Serving 实例（填写 API Base URL 和 API Key）
   - 等用户配置完成后，再告知用户点击编辑器中的「运行」按钮
3. **如果已有 Serving 实例**：告知用户当前使用的 Serving，然后引导用户点击「运行」按钮

### 4. 构建 Pipeline 后同步到编辑器
当你通过工具创建或更新了 pipeline 后，**必须立即**调用 `render_pipeline_in_editor` 工具，
将 pipeline 可视化同步到编辑器，让用户能直观看到节点图。

### 4.1 一次请求只产出一个 pipeline
- **同一轮对话中，最多只调用一次 `create_pipeline`**。不要在收到用户一个需求后，
  反复"写一版 → 不满意 → 再写一版"地调用多次。
- 如果觉得第一版不够好，**继续改进同一条 pipeline 用 `update_pipeline`**，而不是创建新的。
- 用户如果明确说"重新做一个"、"换一种思路"，才允许再创建一次。
- 每次 `create_pipeline` 或 `update_pipeline` 之后**立刻** `render_pipeline_in_editor`，
  等用户反馈再决定是否 `update_pipeline` 继续优化。不要在用户发声之前连续创建多个。

### 5. 操作前告知用户
每次调用工具前，先用一句话告诉用户你要做什么，保持透明。
例如："我来查询一下现有的算子列表……" 或 "我帮你把这个 pipeline 同步到编辑器……"
"""


# 启动时打印一次活跃 CLI 路径，方便确认环境
for _kind in AGENT_KINDS:
    try:
        logger.info(f"AgentSessionManager: {_kind} CLI -> {resolve_cli_path(_kind)}")
    except Exception:
        pass


class AgentSessionManager:
    """
    管理代码 Agent CLI 子进程、当前活跃 session_id（含 agent_kind），
    以及每个用户的历史会话列表。

    运行时内存：
      _current:    user_id -> {"session_id": str, "agent_kind": "claude"|"cursor"|"codex"}
      _adapters:   user_id -> 当前在 stream 的 AgentAdapter 实例（用于 abort）
      _last_active_user_id: 最近一次发起 chat_stream 的 user_id（供 MCP render 定向推送）

    磁盘持久化：
      SESSIONS_FILE = backend/data/agent_sessions.json，结构：
        {
          "<user_id>": {
            "current": "<session_id or null>",
            "current_agent": "claude" | "cursor" | "codex" | null,
            "history": [
              { "session_id": "...", "agent_kind": "claude"|"cursor"|"codex",
                "title": "...",
                "created_at": "...", "updated_at": "...",
                "message_count": N }
            ]
          }
        }
      新会话在首条消息到来时写入；每次 chat 结束后更新 updated_at 与 message_count。
    """

    def __init__(self):
        self._current: dict[str, dict[str, str]] = {}
        self._adapters: dict[str, AgentAdapter] = {}
        self._last_active_user_id: str | None = None
        self._file_lock = threading.Lock()
        self._data: dict = self._load()
        for uid, rec in self._data.items():
            cur_sid = rec.get("current")
            cur_kind = rec.get("current_agent") or DEFAULT_AGENT
            if cur_sid:
                self._current[uid] = {"session_id": cur_sid, "agent_kind": cur_kind}

    # ── 磁盘 I/O ─────────────────────────────────────────────
    def _ensure_storage(self):
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not SESSIONS_FILE.exists():
            SESSIONS_FILE.write_text("{}")

    def _load(self) -> dict:
        self._ensure_storage()
        try:
            content = SESSIONS_FILE.read_text()
            return json.loads(content) if content.strip() else {}
        except Exception:
            return {}

    def _save(self):
        with self._file_lock:
            try:
                SESSIONS_FILE.write_text(
                    json.dumps(self._data, ensure_ascii=False, indent=2)
                )
            except Exception:
                pass

    def _user_record(self, user_id: str) -> dict:
        rec = self._data.get(user_id)
        if not rec:
            rec = {"current": None, "current_agent": None, "history": []}
            self._data[user_id] = rec
        return rec

    def _find_history_entry(self, user_id: str, session_id: str) -> dict | None:
        rec = self._data.get(user_id) or {}
        for item in rec.get("history", []):
            if item.get("session_id") == session_id:
                return item
        return None

    # ── 历史会话 API ─────────────────────────────────────────
    def list_history(self, user_id: str) -> list[dict]:
        rec = self._data.get(user_id) or {}
        items = list(rec.get("history", []))
        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return items

    def new_session(self, user_id: str) -> None:
        """把当前活跃 session 置空；下一轮对话会创建新的 session。"""
        self._current.pop(user_id, None)
        rec = self._user_record(user_id)
        rec["current"] = None
        rec["current_agent"] = None
        self._save()

    def switch_session(self, user_id: str, session_id: str) -> bool:
        """切换到一条历史会话，后续 chat_stream 会沿用它的 agent_kind。"""
        entry = self._find_history_entry(user_id, session_id)
        if not entry:
            return False
        kind = entry.get("agent_kind") or DEFAULT_AGENT
        self._current[user_id] = {"session_id": session_id, "agent_kind": kind}
        rec = self._user_record(user_id)
        rec["current"] = session_id
        rec["current_agent"] = kind
        self._save()
        return True

    def delete_session(self, user_id: str, session_id: str) -> bool:
        rec = self._data.get(user_id)
        if not rec:
            return False
        before = len(rec.get("history", []))
        rec["history"] = [
            h for h in rec.get("history", []) if h.get("session_id") != session_id
        ]
        if rec.get("current") == session_id:
            rec["current"] = None
            rec["current_agent"] = None
            self._current.pop(user_id, None)
        self._save()
        return len(rec["history"]) < before

    def rename_session(self, user_id: str, session_id: str, title: str) -> bool:
        entry = self._find_history_entry(user_id, session_id)
        if not entry:
            return False
        entry["title"] = title
        self._save()
        return True

    # ── Chat 主流程 ─────────────────────────────────────────
    async def chat_stream(
        self,
        user_id: str,
        message: str,
        agent_kind: str | None = None,
    ) -> AsyncGenerator[NormalizedEvent, None]:
        """
        调用所选代码 Agent CLI，以流式方式返回已归一化的 NormalizedEvent。

        ``agent_kind`` 由前端逐次发来；缺省时取上一轮的 kind（同会话不要中途换 agent），
        没有上一轮就用全局默认。
        """
        self._last_active_user_id = user_id

        prior = self._current.get(user_id)
        kind = normalize_agent_kind(
            agent_kind or (prior.get("agent_kind") if prior else None)
        )

        # 切换 agent 等同于开新会话：旧会话的 session_id 对新 agent 没意义
        if prior and prior.get("agent_kind") != kind:
            self._current.pop(user_id, None)
            prior = None

        session_id = prior.get("session_id") if prior else None

        adapter = get_adapter(
            kind,
            webui_root=WEBUI_ROOT,
            mcp_config_path=MCP_CONFIG,
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=ALLOWED_TOOLS,
        )
        self._adapters[user_id] = adapter

        try:
            async for event in adapter.chat_stream(message, session_id=session_id):
                if event.get("type") == "session":
                    sid = event.get("session_id")
                    if sid and (
                        not prior or prior.get("session_id") != sid
                    ):
                        self._current[user_id] = {
                            "session_id": sid,
                            "agent_kind": kind,
                        }
                        rec = self._user_record(user_id)
                        rec["current"] = sid
                        rec["current_agent"] = kind
                        if not self._find_history_entry(user_id, sid):
                            now = datetime.utcnow().isoformat()
                            title = (
                                message.strip().splitlines()[0][:40]
                                if message else "新会话"
                            )
                            rec["history"].append({
                                "session_id": sid,
                                "agent_kind": kind,
                                "title": title,
                                "created_at": now,
                                "updated_at": now,
                                "message_count": 0,
                            })
                        self._save()
                    # `session` 事件不直接抛给前端 —— 前端不需要看到 session_id
                    continue
                yield event
        finally:
            cur = self._current.get(user_id)
            if cur:
                entry = self._find_history_entry(user_id, cur["session_id"])
                if entry:
                    entry["updated_at"] = datetime.utcnow().isoformat()
                    entry["message_count"] = int(entry.get("message_count", 0)) + 1
                    self._save()
            adapter_in_flight = self._adapters.pop(user_id, None)
            if adapter_in_flight is adapter and adapter.is_running:
                adapter.kill()

    # ── 终止 / 清除 ─────────────────────────────────────────
    def abort_session(self, user_id: str):
        """kill 当前子进程，并把当前活跃 session 置空（历史保留）。"""
        adapter = self._adapters.get(user_id)
        if adapter:
            adapter.kill()
        self._adapters.pop(user_id, None)
        self._current.pop(user_id, None)
        rec = self._user_record(user_id)
        rec["current"] = None
        rec["current_agent"] = None
        self._save()

    def clear_session(self, user_id: str):
        """仅脱离当前活跃会话（不 kill 进程、不删历史）。"""
        self._current.pop(user_id, None)
        rec = self._user_record(user_id)
        rec["current"] = None
        rec["current_agent"] = None
        self._save()

    def get_session_id(self, user_id: str) -> str | None:
        cur = self._current.get(user_id)
        return cur["session_id"] if cur else None

    def get_session_agent(self, user_id: str) -> str | None:
        cur = self._current.get(user_id)
        return cur["agent_kind"] if cur else None

    def list_sessions(self) -> dict:
        """当前活跃 session 快照（调试用）。"""
        return dict(self._current)

    def has_active_process(self, user_id: str) -> bool:
        adapter = self._adapters.get(user_id)
        return bool(adapter and adapter.is_running)

    def get_last_active_user_id(self) -> str | None:
        return self._last_active_user_id

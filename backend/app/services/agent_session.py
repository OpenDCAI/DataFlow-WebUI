"""
AgentSessionManager：管理 Claude Code CLI 子进程和会话 ID。
每个 user_id 对应一个"当前活跃"的 claude session_id，并保留一份历史会话列表
以便前端切换 / 恢复旧对话。
"""
import asyncio
import json
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator
from app.core.config import settings

# Claude Code CLI 可执行文件。优先级：
#   1) 环境变量 DATAFLOW_CLAUDE_CLI（显式覆盖）
#   2) 机器上可用的 claude-internal（腾讯内部封装，接口与官方一致）
#   3) 官方 claude
# 需要切回官方：`export DATAFLOW_CLAUDE_CLI=claude` 后重启后端即可。
def _detect_claude_cli() -> str:
    override = os.environ.get("DATAFLOW_CLAUDE_CLI", "").strip()
    if override:
        return override
    if shutil.which("claude-internal"):
        return "claude-internal"
    return "claude"

CLAUDE_CLI = _detect_claude_cli()

# 启动时打印一次，方便确认使用的是 internal 还是官方
try:
    from app.core.logger_setup import get_logger
    get_logger(__name__).info(f"AgentSessionManager will use CLI: {CLAUDE_CLI}")
except Exception:
    pass

# DataFlow-WebUI 根目录（CLI 在此目录运行，自动读取 .mcp.json 和 .claude/skills/）
WEBUI_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# MCP 配置文件路径
MCP_CONFIG = WEBUI_ROOT / ".mcp.json"

# 历史会话持久化路径：backend/<RESOURCE_DIR>/agent_sessions.json
BACKEND_DIR = Path(__file__).parent.parent.parent
SESSIONS_FILE = BACKEND_DIR / settings.RESOURCE_DIR / "agent_sessions.json"

# System prompt：只定义角色边界，Skills 内容由 CLI 自动从 .claude/skills/ 加载
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
    2. 再调 `mcp__dataflow__list_operators` 带 `category=<具体类别>` 参数，只拉你要的那一类（通常 <10KB）
    3. 需要某个算子的完整参数签名时，用 `mcp__dataflow__get_operator_detail_by_name` 按名查单个
- **一轮 reasoning 里 `list_operators` 不超过 2 次**。超过就停下来定下候选集，不要再广撒网。
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


class AgentSessionManager:
    """
    管理 Claude Code CLI 子进程、当前活跃 session_id，以及每个用户的历史会话列表。

    运行时内存：
      _current:    user_id -> 当前活跃的 claude session_id
      _processes:  user_id -> 正在运行的 asyncio subprocess
      _last_active_user_id: 最近一次发起 chat_stream 的 user_id（供 MCP render 定向推送）

    磁盘持久化：
      SESSIONS_FILE = backend/data/agent_sessions.json，结构：
        {
          "<user_id>": {
            "current": "<session_id or null>",
            "history": [
              { "session_id": "...", "title": "...",
                "created_at": "...", "updated_at": "...",
                "message_count": N }
            ]
          }
        }
      新会话在首条消息到来时写入；每次 chat 结束后更新 updated_at 与 message_count。
    """

    def __init__(self):
        self._current: dict[str, str] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._last_active_user_id: str | None = None
        # 进程间无共享（单进程 uvicorn），但 chat_stream 与 REST 可能并发写磁盘
        self._file_lock = threading.Lock()
        self._data: dict = self._load()
        # 把落盘里的 current 恢复到内存
        for uid, rec in self._data.items():
            cur = rec.get("current")
            if cur:
                self._current[uid] = cur

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
            rec = {"current": None, "history": []}
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
        # 按 updated_at 倒序
        items = list(rec.get("history", []))
        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return items

    def new_session(self, user_id: str) -> None:
        """把当前活跃 session 置空；下一轮对话会创建新的 claude session_id。"""
        self._current.pop(user_id, None)
        rec = self._user_record(user_id)
        rec["current"] = None
        self._save()

    def switch_session(self, user_id: str, session_id: str) -> bool:
        """切换到一条历史会话，后续 chat_stream 将用 --resume 继续它。"""
        if not self._find_history_entry(user_id, session_id):
            return False
        self._current[user_id] = session_id
        rec = self._user_record(user_id)
        rec["current"] = session_id
        self._save()
        return True

    def delete_session(self, user_id: str, session_id: str) -> bool:
        rec = self._data.get(user_id)
        if not rec:
            return False
        before = len(rec.get("history", []))
        rec["history"] = [h for h in rec.get("history", []) if h.get("session_id") != session_id]
        if rec.get("current") == session_id:
            rec["current"] = None
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
    ) -> AsyncGenerator[dict, None]:
        """
        调用 Claude Code CLI，以流式方式返回 Agent 输出的每一个 JSON chunk。
        """
        self._last_active_user_id = user_id
        session_id = self._current.get(user_id)
        is_new_session = session_id is None

        cmd = [
            CLAUDE_CLI,
            "--print", message,
            "--output-format", "stream-json",
            "--verbose",
            "--mcp-config", str(MCP_CONFIG),
            "--append-system-prompt", SYSTEM_PROMPT,
            "--allowedTools", "mcp__dataflow__*,Read,Write,Edit",
            "--permission-mode", "dontAsk",
        ]
        if session_id:
            cmd += ["--resume", session_id]

        large_limit = 10 * 1024 * 1024  # 10 MB

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(WEBUI_ROOT),
            limit=large_limit,
        )
        self._processes[user_id] = process

        try:
            async for line in process.stdout:
                line = line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # 首条 chunk 含 session_id，用于登记/更新历史
                sid = chunk.get("session_id")
                if sid and self._current.get(user_id) != sid:
                    self._current[user_id] = sid
                    rec = self._user_record(user_id)
                    rec["current"] = sid
                    if not self._find_history_entry(user_id, sid):
                        now = datetime.utcnow().isoformat()
                        title = message.strip().splitlines()[0][:40] if message else "新会话"
                        rec["history"].append({
                            "session_id": sid,
                            "title": title,
                            "created_at": now,
                            "updated_at": now,
                            "message_count": 0,
                        })
                    self._save()

                yield chunk

        finally:
            # 本轮结束：更新历史 updated_at / message_count
            sid = self._current.get(user_id)
            if sid:
                entry = self._find_history_entry(user_id, sid)
                if entry:
                    entry["updated_at"] = datetime.utcnow().isoformat()
                    entry["message_count"] = int(entry.get("message_count", 0)) + 1
                    self._save()

            self._processes.pop(user_id, None)
            if process.returncode is None:
                try:
                    process.kill()
                except Exception:
                    pass

    # ── 终止 / 清除 ─────────────────────────────────────────
    def abort_session(self, user_id: str):
        """kill 当前子进程，并把当前活跃 session 置空（历史保留）。"""
        process = self._processes.get(user_id)
        if process and process.returncode is None:
            try:
                process.kill()
            except Exception:
                pass
        self._processes.pop(user_id, None)
        self._current.pop(user_id, None)
        rec = self._user_record(user_id)
        rec["current"] = None
        self._save()

    def clear_session(self, user_id: str):
        """仅脱离当前活跃会话（不 kill 进程、不删历史）。"""
        self._current.pop(user_id, None)
        rec = self._user_record(user_id)
        rec["current"] = None
        self._save()

    def get_session_id(self, user_id: str) -> str | None:
        return self._current.get(user_id)

    def list_sessions(self) -> dict:
        """当前活跃 session 快照（调试用）。"""
        return dict(self._current)

    def has_active_process(self, user_id: str) -> bool:
        process = self._processes.get(user_id)
        return process is not None and process.returncode is None

    def get_last_active_user_id(self) -> str | None:
        return self._last_active_user_id

"""
AgentSessionManager：管理 Claude Code CLI 子进程和会话 ID。
每个 user_id 对应一个 claude session_id，实现多轮对话上下文保持。
"""
import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator

# Claude Code CLI 可执行文件（需在 PATH 中，或使用绝对路径）
CLAUDE_CLI = "claude"

# DataFlow-WebUI 根目录（CLI 在此目录运行，自动读取 .mcp.json 和 .claude/skills/）
WEBUI_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# MCP 配置文件路径
MCP_CONFIG = WEBUI_ROOT / ".mcp.json"

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
- **查询算子列表时，必须调用 `mcp__dataflow__list_operators`**，绝对不要用 `Read` 去翻项目目录或源码
- **禁止**用 `Read` 浏览 `/dataflow/`、`/operators/`、`/examples/` 等目录来寻找算子信息
- MCP 工具已提供所有必要的算子和 pipeline 信息，优先使用

### 2. 文件操作：主动执行，不要请求授权
- 当用户提供了文件路径时，**直接用 `Read` 工具读取**，不要询问授权
- 如果用户没有提供样本文件路径但描述了字段结构，**直接用 `Write` 创建示例文件**到 `./data/` 目录，然后继续任务
- 不要说"我需要你的授权"、"请提供文件路径"这类话——直接动手

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

### 5. 操作前告知用户
每次调用工具前，先用一句话告诉用户你要做什么，保持透明。
例如："我来查询一下现有的算子列表……" 或 "我帮你把这个 pipeline 同步到编辑器……"
"""


class AgentSessionManager:
    """
    管理 Claude Code CLI 子进程和 session ID 的映射。

    每次 chat_stream 调用都会：
    1. 检查 user_id 是否有已有的 session_id
    2. 如有，通过 --resume 恢复上下文；如无，开启新会话
    3. 从 CLI 输出的 JSON 流中提取 session_id 并保存

    abort_session 调用会：
    1. 强制 kill 正在运行的 claude 子进程
    2. 清除 session_id 映射，下次对话重新开始
    """

    def __init__(self):
        # user_id → claude session_id 的映射
        self._sessions: dict[str, str] = {}
        # user_id → 当前活跃的 asyncio.subprocess.Process
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def chat_stream(
        self,
        user_id: str,
        message: str,
    ) -> AsyncGenerator[dict, None]:
        """
        调用 Claude Code CLI，以流式方式返回 Agent 输出的每一个 JSON chunk。

        Args:
            user_id: 前端用户标识符（用于恢复会话）
            message: 用户输入的消息文本

        Yields:
            每个 CLI 输出的 JSON 对象（dict）
        """
        session_id = self._sessions.get(user_id)

        cmd = [
            CLAUDE_CLI,
            "--print", message,
            "--output-format", "stream-json",
            "--verbose",
            "--mcp-config", str(MCP_CONFIG),
            "--append-system-prompt", SYSTEM_PROMPT,
            "--allowedTools", "mcp__dataflow__*,Read,Write,Edit",  # dataflow MCP 工具 + 文件读写（不含 Bash）
            "--permission-mode", "dontAsk",         # 禁用交互式权限确认
        ]

        if session_id:
            cmd += ["--resume", session_id]

        # limit 设为 10 MB，防止大型 MCP 响应（如 list_operators ~112KB）触发
        # "Separator is found, but chunk is longer than limit" 错误
        large_limit = 10 * 1024 * 1024  # 10 MB

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(WEBUI_ROOT),  # 在 WebUI 根目录运行，自动读取 .mcp.json 和 .claude/skills/
            limit=large_limit,
        )

        # 注册进程，以便 abort_session 可以强制 kill
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

                # 提取并保存 session_id（首条消息中包含）
                sid = chunk.get("session_id")
                if sid and user_id not in self._sessions:
                    self._sessions[user_id] = sid

                yield chunk

        finally:
            # 无论正常结束、异常还是被取消，都清理进程引用并确保进程退出
            self._processes.pop(user_id, None)
            if process.returncode is None:
                # 进程仍在运行（可能是任务被取消），强制终止
                try:
                    process.kill()
                except Exception:
                    pass

    def abort_session(self, user_id: str):
        """
        强制终止用户的 claude 子进程并清除会话。
        下次对话将重新开始（丢失上下文）。
        """
        process = self._processes.get(user_id)
        if process and process.returncode is None:
            try:
                process.kill()
            except Exception:
                pass
        self._processes.pop(user_id, None)
        self._sessions.pop(user_id, None)

    def clear_session(self, user_id: str):
        """清除指定用户的 session ID，下次对话将重新开始（丢失上下文）。
        注意：不终止正在运行的子进程，如需同时终止进程请使用 abort_session。
        """
        self._sessions.pop(user_id, None)

    def get_session_id(self, user_id: str) -> str | None:
        """获取指定用户的当前 session_id"""
        return self._sessions.get(user_id)

    def list_sessions(self) -> dict:
        """列出所有活跃 session（用于调试）"""
        return dict(self._sessions)

    def has_active_process(self, user_id: str) -> bool:
        """检查用户是否有正在运行的子进程"""
        process = self._processes.get(user_id)
        return process is not None and process.returncode is None

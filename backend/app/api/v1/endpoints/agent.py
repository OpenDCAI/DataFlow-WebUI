"""
WebSocket 端点：前端 ChatPanel 通过此端点与 Agent 进行实时对话。

连接 URL：ws://localhost:8000/api/v1/agent/ws?user_id=<your_user_id>

消息协议（前端 → 后端）：
  { "type": "chat", "message": "用户输入" }
  { "type": "abort_session" }        ← 终止正在运行的 claude 进程并清除当前会话（保留历史）
  { "type": "clear_session" }        ← 脱离当前会话（不 kill 进程），等价于"新建一个对话"
  { "type": "new_session" }          ← 同 clear_session，语义更清晰
  { "type": "switch_session",        ← 切换到一条历史会话，下一轮对话继续它
    "session_id": "..." }

消息协议（后端 → 前端）：
  { "type": "text_chunk", "content": "..." }       ← Agent 回复文本（流式）
  { "type": "tool_call_start", "tool_use_id": "...",
    "name": "mcp__dataflow__list_operators",
    "input_preview": "{ ... }" }                    ← Agent 开始调用某个工具
  { "type": "tool_call_end", "tool_use_id": "...",
    "is_error": false, "output_preview": "..." }    ← 工具调用完成
  { "type": "sync_pipeline", "pipeline": {...},
    "nodes": [...], "edges": [...] }                ← Pipeline 同步到 DAG 编辑器
  { "type": "done" }                               ← 本轮回复完成
  { "type": "session_aborted" }                    ← 会话已终止并清除
  { "type": "session_cleared" }                    ← 会话已清除（新对话，保留历史）
  { "type": "session_switched",                    ← 已切换到历史会话
    "session_id": "..." }
  { "type": "error", "message": "..." }            ← 错误信息
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from app.services.agent_session import AgentSessionManager
from app.core.logger_setup import get_logger
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse
from typing import List, Optional

logger = get_logger(__name__)

router = APIRouter(tags=["agent"])

# 全局 WebSocket 管理器（单例，MCP render_pipeline_in_editor 工具也会用到）
class WebSocketManager:
    """管理所有活跃的 WebSocket 连接，支持定向发送和全局广播"""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}  # user_id → WebSocket

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[user_id] = ws
        logger.info(f"WebSocket connected: user_id={user_id}, total={len(self._connections)}")

    def disconnect(self, user_id: str):
        self._connections.pop(user_id, None)
        logger.info(f"WebSocket disconnected: user_id={user_id}, total={len(self._connections)}")

    async def send(self, user_id: str, data: dict):
        """向指定用户发送消息"""
        ws = self._connections.get(user_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")

    async def broadcast(self, data: dict):
        """向所有已连接用户广播（供 render_pipeline_in_editor MCP 工具调用）"""
        disconnected = []
        for uid, ws in self._connections.items():
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Broadcast failed for user {uid}: {e}")
                disconnected.append(uid)
        for uid in disconnected:
            self.disconnect(uid)

    @property
    def active_connections(self) -> int:
        return len(self._connections)


# 全局单例（在 mcp_server.py 中的 render_pipeline_in_editor 工具需要导入此实例）
ws_manager = WebSocketManager()

# Agent 会话管理器
agent_manager = AgentSessionManager()


@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """
    WebSocket 端点：处理前端 ChatPanel 的实时对话请求。

    查询参数：
        user_id: 用户标识符（默认为 "default"）

    并发模型：
        每次收到 chat 消息后，在 asyncio Task 中运行流式输出，
        同时继续监听 WebSocket（以便接收 abort_session 中断信号）。
    """
    user_id = websocket.query_params.get("user_id", "default")
    await ws_manager.connect(user_id, websocket)

    # 当前活跃的流式任务（每个用户同时只允许一个）
    active_task: asyncio.Task | None = None

    async def run_chat_stream(message: str):
        """在后台 Task 中运行 Agent 流式输出"""
        nonlocal active_task

        def _truncate(obj, limit=400):
            try:
                s = json.dumps(obj, ensure_ascii=False)
            except Exception:
                s = str(obj)
            return s if len(s) <= limit else s[:limit] + "…"

        try:
            async for chunk in agent_manager.chat_stream(
                user_id=user_id,
                message=message,
            ):
                chunk_type = chunk.get("type", "")

                # 标准 Claude Code stream-json 格式：stream_event + text_delta
                if chunk_type == "stream_event":
                    event = chunk.get("event", {})
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        await ws_manager.send(user_id, {
                            "type": "text_chunk",
                            "content": delta.get("text", ""),
                        })

                # Claude Code 格式：type=assistant，完整消息体
                # content 数组中可能包含 text / tool_use 块
                elif chunk_type == "assistant":
                    message_obj = chunk.get("message", {})
                    for content_block in message_obj.get("content", []):
                        block_type = content_block.get("type")
                        if block_type == "text":
                            text = content_block.get("text", "")
                            if text:
                                await ws_manager.send(user_id, {
                                    "type": "text_chunk",
                                    "content": text,
                                })
                        elif block_type == "tool_use":
                            # Agent 开始调用一个工具
                            await ws_manager.send(user_id, {
                                "type": "tool_call_start",
                                "tool_use_id": content_block.get("id", ""),
                                "name": content_block.get("name", ""),
                                "input_preview": _truncate(
                                    content_block.get("input", {})
                                ),
                            })

                # Claude Code 格式：type=result，本轮 agent 循环的最终结束信号
                # （可能因为成功、kvcache 超限、turn 超限等原因结束）
                elif chunk_type == "result":
                    subtype = chunk.get("subtype", "")
                    stop_reason = chunk.get("stop_reason", "")
                    is_error = bool(chunk.get("is_error", False))
                    result_text = chunk.get("result", "") or ""
                    # 只在"异常结束但文本又为空"时推送警告——成功结束由主循环稍后的 done 覆盖
                    if (is_error or stop_reason in (
                        "kvcache_no_enough", "max_turns_exceeded",
                    )) and not result_text.strip():
                        hint = {
                            "kvcache_no_enough":
                                "模型上下文/KV 缓存已塞满，Agent 中止。建议：清空对话重来，"
                                "明确让 Agent 先调 list_operator_categories 再按类别拉算子，"
                                "避免一次性 list_operators。",
                            "max_turns_exceeded":
                                "Agent 工具调用轮次达到上限。建议用更具体的指令或拆小需求再试。",
                        }.get(stop_reason, f"Agent 异常结束（stop_reason={stop_reason}）")
                        await ws_manager.send(user_id, {
                            "type": "error",
                            "message": hint,
                        })

                # Claude Code 格式：type=user，通常是工具执行结果回填
                elif chunk_type == "user":
                    message_obj = chunk.get("message", {})
                    for content_block in message_obj.get("content", []):
                        if content_block.get("type") == "tool_result":
                            output = content_block.get("content", "")
                            # content 可能是字符串或 content block 列表
                            if isinstance(output, list):
                                output = "".join(
                                    (b.get("text", "") if isinstance(b, dict) else str(b))
                                    for b in output
                                )
                            await ws_manager.send(user_id, {
                                "type": "tool_call_end",
                                "tool_use_id": content_block.get("tool_use_id", ""),
                                "is_error": bool(content_block.get("is_error", False)),
                                "output_preview": _truncate(output),
                            })

            # 本轮回复正常完成
            await ws_manager.send(user_id, {"type": "done"})
            logger.info(f"[{user_id}] Round complete")

        except asyncio.CancelledError:
            # 被 abort_session 取消：发送 done 使前端恢复输入框
            await ws_manager.send(user_id, {"type": "done"})
            logger.info(f"[{user_id}] Stream cancelled by abort")
        except Exception as e:
            logger.error(f"[{user_id}] Stream error: {e}", exc_info=True)
            await ws_manager.send(user_id, {"type": "error", "message": str(e)})
            await ws_manager.send(user_id, {"type": "done"})
        finally:
            active_task = None

    try:
        while True:
            raw = await websocket.receive_json()
            msg_type = raw.get("type", "chat")

            if msg_type == "chat":
                user_message = raw.get("message", "").strip()
                if not user_message:
                    continue

                # 如果上一轮还在跑，先中止它
                if active_task and not active_task.done():
                    agent_manager.abort_session(user_id)
                    active_task.cancel()
                    try:
                        await active_task
                    except (asyncio.CancelledError, Exception):
                        pass

                logger.info(f"[{user_id}] Received message: {user_message[:80]}...")

                # 在后台 Task 中运行，主循环继续监听 WebSocket
                active_task = asyncio.create_task(run_chat_stream(user_message))

            elif msg_type == "abort_session":
                # 终止正在运行的 claude 进程，清除会话上下文
                if active_task and not active_task.done():
                    active_task.cancel()
                    try:
                        await active_task
                    except (asyncio.CancelledError, Exception):
                        pass
                agent_manager.abort_session(user_id)
                await ws_manager.send(user_id, {"type": "session_aborted"})
                logger.info(f"[{user_id}] Session aborted")

            elif msg_type == "clear_session" or msg_type == "new_session":
                # 脱离当前会话（不 kill 进程、保留历史），等价于"新建一个对话"
                agent_manager.clear_session(user_id)
                await ws_manager.send(user_id, {"type": "session_cleared"})
                logger.info(f"[{user_id}] Session cleared")

            elif msg_type == "switch_session":
                sid = (raw.get("session_id") or "").strip()
                if not sid:
                    await ws_manager.send(user_id, {
                        "type": "error", "message": "switch_session requires session_id",
                    })
                    continue
                # 正在跑的流需要先中止，避免和旧 session 的子进程纠缠
                if active_task and not active_task.done():
                    active_task.cancel()
                    try:
                        await active_task
                    except (asyncio.CancelledError, Exception):
                        pass
                ok_switch = agent_manager.switch_session(user_id, sid)
                if ok_switch:
                    await ws_manager.send(user_id, {
                        "type": "session_switched", "session_id": sid,
                    })
                    logger.info(f"[{user_id}] Switched to session {sid}")
                else:
                    await ws_manager.send(user_id, {
                        "type": "error",
                        "message": f"Session {sid} not found for this user",
                    })

    except WebSocketDisconnect:
        # 前端断开连接：清理后台任务
        if active_task and not active_task.done():
            active_task.cancel()
            try:
                await active_task
            except (asyncio.CancelledError, Exception):
                pass
        ws_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"[{user_id}] WebSocket error: {e}", exc_info=True)
        if active_task and not active_task.done():
            active_task.cancel()
        try:
            await ws_manager.send(user_id, {"type": "error", "message": str(e)})
        except Exception:
            pass
        ws_manager.disconnect(user_id)


# ─── Session history REST API ────────────────────────────────────────────────

class SessionInfo(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class SessionListOut(BaseModel):
    current: Optional[str] = None
    history: List[SessionInfo] = []


class RenameSessionIn(BaseModel):
    title: str


@router.get(
    "/sessions",
    response_model=ApiResponse[SessionListOut],
    summary="列出指定 user 的历史 Agent 会话",
)
def list_agent_sessions(user_id: str = "default"):
    history = agent_manager.list_history(user_id)
    return ok(SessionListOut(
        current=agent_manager.get_session_id(user_id),
        history=[SessionInfo(**h) for h in history],
    ))


@router.delete(
    "/sessions/{session_id}",
    response_model=ApiResponse[dict],
    summary="删除一条历史 Agent 会话",
)
def delete_agent_session(session_id: str, user_id: str = "default"):
    removed = agent_manager.delete_session(user_id, session_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Session not found")
    return ok({"deleted": True, "session_id": session_id})


@router.put(
    "/sessions/{session_id}",
    response_model=ApiResponse[dict],
    summary="重命名一条历史 Agent 会话",
)
def rename_agent_session(session_id: str, body: RenameSessionIn, user_id: str = "default"):
    renamed = agent_manager.rename_session(user_id, session_id, body.title.strip())
    if not renamed:
        raise HTTPException(status_code=404, detail="Session not found")
    return ok({"session_id": session_id, "title": body.title.strip()})

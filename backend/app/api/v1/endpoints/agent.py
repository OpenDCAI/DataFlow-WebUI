"""
WebSocket 端点：前端 ChatPanel 通过此端点与 Agent 进行实时对话。

连接 URL：ws://localhost:8000/api/v1/agent/ws?user_id=<your_user_id>

消息协议（前端 → 后端）：
  { "type": "chat", "message": "用户输入" }
  { "type": "abort_session" }     ← 终止正在运行的 claude 进程并清除上下文
  { "type": "clear_session" }     ← 仅清除上下文（不终止进程，已废弃，保留兼容）

消息协议（后端 → 前端）：
  { "type": "text_chunk", "content": "..." }       ← Agent 回复文本（流式）
  { "type": "sync_pipeline", "pipeline": {...},
    "nodes": [...], "edges": [...] }                ← Pipeline 同步到 DAG 编辑器
  { "type": "done" }                               ← 本轮回复完成
  { "type": "session_aborted" }                    ← 会话已终止并清除
  { "type": "session_cleared" }                    ← 会话已清除（兼容旧版）
  { "type": "error", "message": "..." }            ← 错误信息
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.agent_session import AgentSessionManager
from app.core.logger_setup import get_logger

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
                elif chunk_type == "assistant":
                    message_obj = chunk.get("message", {})
                    for content_block in message_obj.get("content", []):
                        if content_block.get("type") == "text":
                            text = content_block.get("text", "")
                            if text:
                                await ws_manager.send(user_id, {
                                    "type": "text_chunk",
                                    "content": text,
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

            elif msg_type == "clear_session":
                # 兼容旧版：仅清除 session ID（不强制终止进程）
                agent_manager.clear_session(user_id)
                await ws_manager.send(user_id, {"type": "session_cleared"})
                logger.info(f"[{user_id}] Session cleared")

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

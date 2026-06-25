"""
MCP Server：将 DataFlow 后端操作暴露为 Agent 可调用的工具。
通过 FastAPI-MCP 库挂载到主 FastAPI app，同时将 render_pipeline_in_editor
注册为一个真实的 FastAPI 路由，再由 FastApiMCP 自动暴露为 MCP 工具。
"""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from app.core.logger_setup import get_logger

logger = get_logger(__name__)

_mcp_instance: FastApiMCP = None


def create_mcp_server(app: FastAPI) -> FastApiMCP:
    """
    创建并挂载 MCP Server 到 FastAPI app。
    挂载路径为 /mcp，Claude Code CLI 通过项目根目录的 .mcp.json 自动连接此地址。
    """
    global _mcp_instance

    # 先注册自定义路由，再让 FastApiMCP 扫描
    _register_render_pipeline_route(app)

    mcp = FastApiMCP(
        app,
        name="DataFlow MCP Server",
        description="Tools for managing DataFlow pipelines, tasks, operators and datasets",
        # 白名单：只暴露安全的只读/创建操作 + 自定义同步工具
        include_operations=[
            "list_operator_categories",         # GET /api/v1/operators/categories  ← 便宜入口，带 use_for/not_for 指引；agent 必须先调
            "recommend_operator_categories",    # POST /api/v1/operators/recommend_categories  ← 结合任务描述/列名给出最多 2 个候选 category
            "list_operators",                   # GET /api/v1/operators/by_category?category=xxx  category 必填，缺省/非法会 40010/40011
            "get_operator_detail_by_name",      # GET /api/v1/operators/details/{name} 单个算子详情
            "list_pipelines",                   # GET /api/v1/pipelines/
            "create_pipeline",                  # POST /api/v1/pipelines/
            "update_pipeline",                  # PUT /api/v1/pipelines/{pipeline_id}
            "get_pipeline",                     # GET /api/v1/pipelines/{pipeline_id}
            "execute_pipeline",                 # POST /api/v1/tasks/execute
            "execute_pipeline_async",           # POST /api/v1/tasks/execute-async
            "get_execution_status",             # GET /api/v1/tasks/execution/{task_id}/status
            "get_task_result",                  # GET /api/v1/tasks/execution/{task_id}/result
            "list_datasets",                    # GET /api/v1/datasets/
            "get_dataset_columns",              # GET /api/v1/datasets/columns/{ds_id}
            "get_dataset_preview",              # GET /api/v1/datasets/preview/{ds_id}  ← 必须在设置 lang 等语义参数前调用，agent 凭样本判断数据语言
            "register_dataset",                 # POST /api/v1/datasets/
            "list_serving",                     # GET /api/v1/serving/
            "list_servings",                    # GET /api/v1/serving/plural_alias (backward-compatible alias)
            "validate_pipeline_config",         # POST /api/v1/pipelines/validate
            "render_pipeline_in_editor",        # POST /api/v1/agent/render (自定义)
        ],
    )
    mcp.mount()  # 挂载到 /mcp 路径

    _mcp_instance = mcp
    logger.info("MCP Server mounted at /mcp")

    return mcp


def _register_render_pipeline_route(app: FastAPI):
    """
    将 render_pipeline_in_editor 注册为 FastAPI 路由。
    FastApiMCP 会自动将其暴露为 MCP 工具。
    """
    from pydantic import BaseModel

    class RenderRequest(BaseModel):
        pipeline_id: str

    class RenderResponse(BaseModel):
        status: str
        message: str
        nodes_count: int = 0
        edges_count: int = 0

    @app.post(
        "/api/v1/agent/render",
        operation_id="render_pipeline_in_editor",
        summary="Render pipeline in DAG editor",
        description=(
            "将指定 pipeline 的配置同步渲染到前端 DAG 编辑器中。"
            "调用此工具后，所有已连接的前端页面将自动刷新显示新的 pipeline 节点图。"
            "当你构建或修改好 pipeline 后，请主动调用此工具让用户看到可视化效果。"
        ),
        response_model=RenderResponse,
        tags=["agent"],
    )
    async def render_pipeline_in_editor(req: RenderRequest) -> RenderResponse:
        from app.core.container import container
        from app.api.v1.endpoints.agent import ws_manager, agent_manager

        pipeline = container.pipeline_registry.get_pipeline(req.pipeline_id)
        if not pipeline:
            return RenderResponse(
                status="error",
                message=f"Pipeline {req.pipeline_id} not found",
            )

        nodes, edges = _config_to_vue_flow(pipeline.get("config", {}))
        payload = {
            "type": "sync_pipeline",
            "pipeline": pipeline,                 # ← 关键：前端 renderPipeline() 用这个（完整 config）
            "pipeline_id": req.pipeline_id,
            # 下面两个是给旧消费者的兼容字段，真正的渲染走 pipeline.config
            "nodes": nodes,
            "edges": edges,
        }
        # 优先向"最近发起对话的用户"定向推送，避免串扰到其他浏览器窗口。
        # 仅在没有已知活跃用户时回退为广播。
        target_uid = agent_manager.get_last_active_user_id()
        if target_uid:
            await ws_manager.send(target_uid, payload)
            logger.info(
                f"Pipeline {req.pipeline_id} synced to editor for user={target_uid} "
                f"({len(nodes)} nodes, {len(edges)} edges)"
            )
        else:
            await ws_manager.broadcast(payload)
            logger.info(
                f"Pipeline {req.pipeline_id} broadcast to all editors "
                f"({len(nodes)} nodes, {len(edges)} edges)"
            )
        return RenderResponse(
            status="ok",
            message=f"Pipeline '{pipeline.get('name', req.pipeline_id)}' 已同步到编辑器",
            nodes_count=len(nodes),
            edges_count=len(edges),
        )


def _config_to_vue_flow(config: dict) -> tuple[list, list]:
    """
    将 DataFlow pipeline config 转换为 Vue Flow 所需的 nodes/edges 格式。

    节点布局：从左到右水平排列，间距 250px。
    如果算子配置中包含 location 字段（[x, y]），则使用该位置。
    """
    operators = config.get("operators", [])
    nodes: list = []
    edges: list = []

    for i, op in enumerate(operators):
        node_id = f"op_{i}"
        location = op.get("location", [250 * i + 100, 200])
        nodes.append({
            "id": node_id,
            "type": "operator",
            "position": {"x": location[0], "y": location[1]},
            "data": {
                "label": op["name"],
                "params": op.get("params", {}),
            },
        })
        if i > 0:
            edges.append({
                "id": f"e_{i-1}_{i}",
                "source": f"op_{i-1}",
                "target": node_id,
                "type": "smoothstep",
            })

    return nodes, edges


def get_mcp_instance() -> FastApiMCP:
    """获取全局 MCP 实例（用于调试）"""
    return _mcp_instance

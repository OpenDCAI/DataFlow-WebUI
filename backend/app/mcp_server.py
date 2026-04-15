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
            "list_operators",                   # GET /api/v1/operators/
            "list_pipelines",                   # GET /api/v1/pipelines/
            "create_pipeline",                  # POST /api/v1/pipelines/
            "update_pipeline",                  # PUT /api/v1/pipelines/{pipeline_id}
            "get_pipeline",                     # GET /api/v1/pipelines/{pipeline_id}
            "execute_pipeline",                 # POST /api/v1/tasks/execute
            "execute_pipeline_async",           # POST /api/v1/tasks/execute-async
            "get_execution_status",             # GET /api/v1/tasks/execution/{task_id}/status
            "get_task_result",                  # GET /api/v1/tasks/execution/{task_id}/result
            "list_datasets",                    # GET /api/v1/datasets/
            "list_serving",                     # GET /api/v1/serving/
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
        from app.api.v1.endpoints.agent import ws_manager

        pipeline = container.pipeline_registry.get_pipeline(req.pipeline_id)
        if not pipeline:
            return RenderResponse(
                status="error",
                message=f"Pipeline {req.pipeline_id} not found",
            )

        nodes, edges = _config_to_vue_flow(pipeline.get("config", {}))
        await ws_manager.broadcast({
            "type": "sync_pipeline",
            "pipeline": pipeline,
            "nodes": nodes,
            "edges": edges,
        })
        logger.info(
            f"Pipeline {req.pipeline_id} synced to editor "
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

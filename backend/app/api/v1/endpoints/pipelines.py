from typing import List, Dict
from fastapi import APIRouter, HTTPException, Request
from app.schemas.pipelines import (
    PipelineIn,
    PipelineOut,
    PipelineUpdateIn,
)
from app.core.container import container
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse
from app.core.logger_setup import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(tags=["pipelines"])

@router.get("/", response_model=ApiResponse[List[PipelineOut]], operation_id="list_pipelines", summary="返回所有注册的Pipeline列表")
def list_pipelines(request: Request):
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        pipelines = container.pipeline_registry.list_pipelines()
        logger.info(f"Successfully listed {len(pipelines)} pipelines")
        return ok(pipelines)
    except Exception as e:
        logger.error(f"Failed to list pipelines: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to list pipelines: {str(e)}")


@router.get("/templates", response_model=ApiResponse[List[PipelineOut]], operation_id="list_template_pipelines", summary="返回所有预置(template) Pipeline列表")
def list_template_pipelines(request: Request):
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        pipelines = container.pipeline_registry.list_templates()
        logger.info(f"Successfully listed {len(pipelines)} template pipelines")
        return ok(pipelines)
    except Exception as e:
        logger.error(f"Failed to list template pipelines: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to list template pipelines: {str(e)}")

@router.post("/", response_model=ApiResponse[PipelineOut], operation_id="create_pipeline", summary="创建一个新的Pipeline")
def create_pipeline(request: Request, payload: PipelineIn):
    try:
        logger.info(f"Request: {request.method} {request.url.path}, Pipeline name: {payload.name}")
        pipeline_in_data = payload.model_dump()

        operators = pipeline_in_data.get("config", {}).get("operators", [])
        for op in operators:
            op["params"] = container.pipeline_registry._parse_frontend_params(op.get("params", []))

        pipeline = container.pipeline_registry.create_pipeline(pipeline_in_data)
        return created(pipeline)
    except ValueError as e:
        logger.error(f"Invalid pipeline configuration: {str(e)}", exc_info=True)
        raise HTTPException(400, f"Invalid pipeline configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create pipeline: {str(e)}", exc_info=True)
        raise HTTPException(400, f"Failed to create pipeline: {str(e)}")

@router.get("/{pipeline_id}", response_model=ApiResponse[PipelineOut], operation_id="get_pipeline", summary="根据ID获取Pipeline详情")
def get_pipeline(pipeline_id: str):
    pipeline = container.pipeline_registry.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"Pipeline with id {pipeline_id} not found")
    return ok(pipeline)

@router.put("/{pipeline_id}", response_model=ApiResponse[PipelineOut], operation_id="update_pipeline", summary="更新指定的Pipeline")
def update_pipeline(pipeline_id: str, payload: PipelineUpdateIn):
    try:
        pipeline_in_data = payload.model_dump(exclude_unset=True)

        # operators = pipeline_in_data.get("config", {}).get("operators", [])
        # for op in operators:
        #     op["params"] = container.pipeline_registry.parse_frontend_params(op.get("params", []))

        updated_pipeline = container.pipeline_registry.update_pipeline(pipeline_id, pipeline_in_data)
        return ok(updated_pipeline)
    except ValueError as e:
        logger.error(f"Failed to update pipeline: {str(e)}")
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to update pipeline {pipeline_id}: {e}")
        raise HTTPException(400, f"Failed to update pipeline: {e}")

@router.delete("/{pipeline_id}", response_model=ApiResponse[Dict], operation_id="delete_pipeline", summary="删除指定的Pipeline") 
def delete_pipeline(pipeline_id: str):
    try:
        success = container.pipeline_registry.delete_pipeline(pipeline_id)
        if not success:
            raise HTTPException(404, f"Pipeline with id {pipeline_id} not found")
        return ok(message=f"Pipeline {pipeline_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete pipeline {pipeline_id}: {e}")
        raise HTTPException(500, f"Failed to delete pipeline: {e}")


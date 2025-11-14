from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from app.schemas.pipelines import (
    PipelineIn,
    PipelineOut,
    PipelineExecutionRequest, 
    PipelineExecutionResult
)
from app.services.pipeline_registry import PipelineRegistry, _PIPELINE_REGISTRY
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse
from app.core.logger_setup import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(tags=["pipelines"])

# CRUD操作API
@router.get("/", response_model=ApiResponse[List[PipelineOut]], operation_id="list_pipelines", summary="返回所有注册的Pipeline列表")
def list_pipelines(request: Request):
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        pipelines = _PIPELINE_REGISTRY.list_pipelines()
        logger.info(f"Successfully listed {len(pipelines)} pipelines")
        return ok(pipelines)
    except Exception as e:
        logger.error(f"Failed to list pipelines: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to list pipelines: {str(e)}")

@router.post("/", response_model=ApiResponse[PipelineOut], operation_id="create_pipeline", summary="创建一个新的Pipeline")
def create_pipeline(request: Request, payload: PipelineIn):
    try:
        logger.info(f"Request: {request.method} {request.url.path}, Pipeline name: {payload.name}")
        pipeline = _PIPELINE_SERVICE.create_pipeline(payload)
        return created(pipeline)
    except ValueError as e:
        logger.error(f"Invalid pipeline configuration: {str(e)}", exc_info=True)
        raise HTTPException(400, f"Invalid pipeline configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create pipeline: {str(e)}", exc_info=True)
        raise HTTPException(400, f"Failed to create pipeline: {str(e)}")

@router.get("/{pipeline_id}", response_model=ApiResponse[PipelineOut], operation_id="get_pipeline", summary="根据ID获取Pipeline详情")
def get_pipeline(pipeline_id: str):
    pipeline = _PIPELINE_SERVICE.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(404, f"Pipeline with id {pipeline_id} not found")
    return ok(pipeline)

@router.put("/{pipeline_id}", response_model=ApiResponse[PipelineOut], operation_id="update_pipeline", summary="更新指定的Pipeline")
def update_pipeline(pipeline_id: str, payload: PipelineIn):
    try:
        updated_pipeline = _PIPELINE_SERVICE.update_pipeline(pipeline_id, payload)
        return ok(updated_pipeline)
    except ValueError as e:
        logger.error(f"Failed to update pipeline: {str(e)}")
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to update pipeline {pipeline_id}: {e}")
        raise HTTPException(400, f"Failed to update pipeline: {e}")

@router.delete("/{pipeline_id}", operation_id="delete_pipeline", summary="删除指定的Pipeline")
def delete_pipeline(pipeline_id: str):
    try:
        success = _PIPELINE_SERVICE.delete_pipeline(pipeline_id)
        if not success:
            raise HTTPException(404, f"Pipeline with id {pipeline_id} not found")
        return ok(message=f"Pipeline {pipeline_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete pipeline {pipeline_id}: {e}")
        raise HTTPException(500, f"Failed to delete pipeline: {e}")

# Pipeline执行API
@router.post("/execute", response_model=ApiResponse[PipelineExecutionResult], operation_id="execute_pipeline", summary="执行Pipeline")
async def execute_pipeline(request: Request, payload: PipelineExecutionRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # 调用服务层开始执行
        execution_id, pipeline_config, initial_result = _PIPELINE_SERVICE.start_execution(
            pipeline_id=payload.pipeline_id, 
            config=payload.config
        )
        
        # 在后台异步执行Pipeline
        background_tasks.add_task(
            _PIPELINE_SERVICE.execute_pipeline_task, 
            execution_id, 
            pipeline_config
        )
        
        return ok(initial_result, message="Pipeline execution started")
    except ValueError as e:
        logger.error(f"Invalid execution request: {str(e)}")
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start pipeline execution: {e}")
        raise HTTPException(400, f"Failed to start pipeline execution: {e}")

@router.get("/execution/{execution_id}", response_model=ApiResponse[PipelineExecutionResult], operation_id="get_execution_result", summary="获取Pipeline执行结果")
def get_execution_result(execution_id: str):
    result = _PIPELINE_SERVICE.get_execution_result(execution_id)
    if not result:
        raise HTTPException(404, f"Execution with id {execution_id} not found")
    return ok(result)

@router.get("/executions", response_model=ApiResponse[List[PipelineExecutionResult]], operation_id="list_executions", summary="列出所有Pipeline执行记录")
def list_executions():
    try:
        executions = _PIPELINE_SERVICE.list_executions()
        return ok(executions)
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(500, f"Failed to list executions: {e}")
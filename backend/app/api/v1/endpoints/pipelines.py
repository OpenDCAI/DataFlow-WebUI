from typing import List, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from app.schemas.pipelines import (
    PipelineIn,
    PipelineOut,
    PipelineUpdateIn,
    PipelineExecutionRequest, 
    PipelineExecutionResult
)
from app.core.container import container
from app.services.dataflow_engine import dataflow_engine
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse
from app.core.logger_setup import get_logger

# 配置日志
logger = get_logger(__name__)

# 创建路由器
router = APIRouter(tags=["pipelines"])

# CRUD操作API
@router.get("/executions", response_model=ApiResponse[List[PipelineExecutionResult]], operation_id="list_executions", summary="列出所有Pipeline执行记录")
def list_executions():
    try:
        print("Where am I?")
        executions = container.pipeline_registry.list_executions()
        return ok(executions)
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(500, f"Failed to list executions: {e}")

@router.get("/execution/{execution_id}", response_model=ApiResponse[PipelineExecutionResult], operation_id="get_execution_result", summary="获取Pipeline执行结果")
def get_execution_result(execution_id: str):
    result = container.pipeline_registry.get_execution_result(execution_id)
    if not result:
        raise HTTPException(404, f"Execution with id {execution_id} not found")
    return ok(result)


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

@router.post("/", response_model=ApiResponse[PipelineOut], operation_id="create_pipeline", summary="创建一个新的Pipeline")
def create_pipeline(request: Request, payload: PipelineIn):
    try:
        logger.info(f"Request: {request.method} {request.url.path}, Pipeline name: {payload.name}")
        pipeline_in_data = payload.model_dump()

        operators = pipeline_in_data.get("config", {}).get("operators", [])
        for op in operators:
            op["params"] = container.pipeline_registry.parse_frontend_params(op.get("params", []))

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

# Pipeline执行API
@router.post("/execute", response_model=ApiResponse[PipelineExecutionResult], operation_id="execute_pipeline", summary="执行Pipeline")
async def execute_pipeline(request: Request, pipeline_id):
    execution_id = None
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        
        pipeline_config = container.pipeline_registry.get_pipeline(pipeline_id)
        if not pipeline_config:
            raise HTTPException(404, f"Pipeline {pipeline_id} not found")

        # 调用服务层开始执行
        execution_id, _, initial_result = container.pipeline_registry.start_execution(
            pipeline_id=pipeline_id, 
            config=pipeline_config
        )
        logger.info(f"Execution ID: {execution_id}")
        
        # 执行 pipeline (run 方法内部已经处理所有异常，总是返回结果)
        result = dataflow_engine.run(pipeline_config["config"], execution_id)
        
        # 更新执行记录到 registry
        data = container.pipeline_registry._read()
        if execution_id in data.get("executions", {}):
            data["executions"][execution_id].update(result)
            container.pipeline_registry._write(data)
        
        return ok(result, message=f"Pipeline execution {result['status']}")
        
    except HTTPException:
        raise
    except Exception as e:
        # 导入 DataFlowEngineError 来检查异常类型
        from app.services.dataflow_engine import DataFlowEngineError
        
        if isinstance(e, DataFlowEngineError):
            # 详细的错误信息
            error_detail = e.to_dict()
            logger.error(f"Pipeline execution failed: {e.message}")
            logger.error(f"Context: {e.context}")
            if e.traceback_str:
                logger.error(f"Traceback: {e.traceback_str}")
            
            # 如果有 execution_id，更新执行状态为 failed
            if execution_id:
                try:
                    data = container.pipeline_registry._read()
                    if execution_id in data.get("executions", {}):
                        data["executions"][execution_id].update({
                            "status": "failed",
                            "output": {
                                "error": e.message,
                                "context": e.context,
                                "original_error": str(e.original_error) if e.original_error else None
                            },
                            "completed_at": datetime.now().isoformat()
                        })
                        container.pipeline_registry._write(data)
                except Exception as update_error:
                    logger.error(f"Failed to update execution status: {update_error}")
            
            # 返回详细的错误信息给客户端
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Pipeline执行失败: {e.message}",
                    "error_details": error_detail
                }
            )
        else:
            # 普通异常
            logger.error(f"Failed to execute pipeline {pipeline_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(500, f"Failed to execute pipeline: {str(e)}")

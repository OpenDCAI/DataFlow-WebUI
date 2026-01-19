from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from typing import List, Dict
from app.schemas.pipelines import (
    PipelineExecutionResult
)
from app.services.dataflow_engine import dataflow_engine
from app.core.container import container
from app.api.v1.envelope import ApiResponse
from app.api.v1.resp import ok
from app.api.v1.errors import *
from datetime import datetime
from app.core.logger_setup import get_logger
import os

# 配置日志
logger = get_logger(__name__)

router = APIRouter(tags=["tasks"])


# CRUD操作API
@router.get("/executions", response_model=ApiResponse[List[PipelineExecutionResult]], operation_id="list_executions", summary="列出所有Pipeline执行记录")
def list_executions():
    try:
        executions = container.task_registry.list_executions()
        return ok(executions)
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(500, f"Failed to list executions: {e}")

@router.get("/execution/{task_id}/status", response_model=ApiResponse[Dict], operation_id="get_execution_status", summary="查询Pipeline执行状态（算子粒度）")
def get_execution_status(task_id: str):
    """
    查询任务执行状态（包含算子粒度）
    
    Args:
        task_id: 任务 ID
    
    Returns:
        执行状态字典，包含每个算子的执行状态
    """
    try:
        logger.info(f"Request: GET /execution/{task_id}/status")
        
        status = container.task_registry.get_execution_status(task_id)
        if not status:
            raise HTTPException(404, f"Task with id {task_id} not found")
        
        return ok(status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(500, f"Failed to get task status: {str(e)}")

@router.get("/execution/{task_id}/result", response_model=ApiResponse[Dict], operation_id="get_task_result", summary="查询任务执行结果")
def get_task_result(task_id: str, step: int = None, limit: int = 5):
    """
    查询任务执行结果
    
    Args:
        task_id: 任务 ID
        step: 步骤索引（可选，None 表示返回最后一个步骤的输出）
        limit: 返回的数据条数（默认5条）
    
    Returns:
        执行结果字典
    """
    try:
        logger.info(f"Request: GET /execution/{task_id}/result, step={step}, limit={limit}")
        
        result = container.task_registry.get_execution_result(task_id, step, limit)
        if not result:
            raise HTTPException(404, f"Task with id {task_id} not found")
        
        return ok(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task result: {e}")
        raise HTTPException(500, f"Failed to get task result: {str(e)}")


@router.get("/execution/{task_id}/log", response_model=ApiResponse[List[str]], operation_id="get_execution_log", summary="获取任务日志")
def get_execution_log(task_id: str, operator_name: str = Query(None, description="算子名称")):
    """
    获取任务日志
    
    Args:
        task_id: 任务 ID
        operator_name: 算子名称（可选，指定时返回该算子的日志）
    
    Returns:
        日志列表
    """
    try:
        logger.info(f"Request: GET /execution/{task_id}/log, operator_name={operator_name}")
        
        # 检查任务是否存在
        task = container.task_registry.get(task_id)
        if not task:
            raise HTTPException(404, f"Task with id {task_id} not found")

        logs = container.task_registry.get_execution_logs(task_id, operator_name)
        
        return ok(logs)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task logs: {e}")
        raise HTTPException(500, f"Failed to get task logs: {str(e)}")


@router.get("/execution/{task_id}/download", operation_id="download_task_result", summary="下载任务执行结果文件")
def download_task_result(task_id: str, step: int = None):
    """
    下载任务执行结果文件
    
    Args:
        task_id: 任务 ID
        step: 步骤索引（可选，None 表示下载最后一个已完成的步骤）
    
    Returns:
        文件下载响应
    """
    try:
        logger.info(f"Request: GET /execution/{task_id}/download, step={step}")
        
        # 获取执行记录
        data = container.task_registry._read()
        execution_data = data.get("tasks", {}).get(task_id)
        
        if not execution_data:
            raise HTTPException(404, f"Task with id {task_id} not found")
        
        # 获取执行结果
        output = execution_data.get("output", {})
        execution_results = output.get("execution_results", [])
        
        # 确定要下载的步骤索引
        if step is None:
            # 默认下载最后一个已完成的步骤
            if execution_results:
                step = execution_results[-1].get("index", 0)
            else:
                raise HTTPException(400, "No completed operators found")
        
        # 检查步骤是否有效
        if step < 0 or step >= len(execution_results):
            raise HTTPException(400, f"Invalid step index: {step}. Valid range: 0-{len(execution_results)-1}")
        
        # 获取算子信息
        operator_info = execution_results[step]
        operator_name = operator_info.get("operator", f"step_{step}")
        
        # 构建缓存文件路径（使用绝对路径）
        from app.core.config import settings
        cache_path = settings.CACHE_DIR
        cache_file_prefix = "dataflow_cache_step"
        cache_file = os.path.join(cache_path, f"{cache_file_prefix}_step{step}.jsonl")
        
        # 检查文件是否存在
        if not os.path.exists(cache_file):
            raise HTTPException(404, f"Result file not found for step {step}: {cache_file}")
        
        # 返回文件下载
        filename = f"{task_id}_{operator_name}_step{step}.jsonl"
        logger.info(f"Downloading file: {cache_file} as {filename}")
        
        return FileResponse(
            path=cache_file,
            filename=filename,
            media_type="application/jsonl",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download execution result: {e}")
        raise HTTPException(500, f"Failed to download execution result: {str(e)}")


# Pipeline执行API
@router.post("/execute", response_model=ApiResponse[PipelineExecutionResult], operation_id="execute_pipeline", summary="执行Pipeline")
async def execute_pipeline(request: Request, pipeline_id):
    task_id = None
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        
        pipeline_config = container.pipeline_registry.get_pipeline(pipeline_id)
        if not pipeline_config:
            raise HTTPException(404, f"Pipeline {pipeline_id} not found")

        # 调用服务层开始执行
        task_id, _, initial_result = container.task_registry.start_execution(
            pipeline_id=pipeline_id, 
            config=pipeline_config
        )
        logger.info(f"Execution ID: {task_id}")
        
        # 执行 pipeline (run 方法内部已经处理所有异常，总是返回结果)
        result = dataflow_engine.run(pipeline_config["config"], task_id, execution_path=container.task_registry.path)
        
        # 更新执行记录到 registry
        data = container.task_registry._read()
        if task_id in data.get("tasks", {}):
            data["tasks"][task_id].update(result)
            container.task_registry._write(data)
        
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
            
            # 如果有 task_id，更新执行状态为 failed
            if task_id:
                try:
                    data = container.task_registry._read()
                    if task_id in data.get("tasks", {}):
                        data["tasks"][task_id].update({
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


@router.post("/execute-async", response_model=ApiResponse[Dict], operation_id="execute_pipeline_async", summary="异步执行Pipeline（使用Ray）")
async def execute_pipeline_async(request: Request, pipeline_id: str):
    """
    异步执行 Pipeline
    
    使用 Ray 进行异步执行，立即返回 task_id 和 task_id
    客户端可以通过 GET /execution/{task_id}/status 轮询执行状态
    """
    try:
        logger.info(f"Request: {request.method} {request.url.path}")
        
        pipeline_config = container.pipeline_registry.get_pipeline(pipeline_id)
        if not pipeline_config:
            raise HTTPException(404, f"Pipeline {pipeline_id} not found")

        # 调用服务层开始异步执行
        result = await container.task_registry.start_execution_async(
            pipeline_id=pipeline_id
        )
        task_id = result["task_id"]
        logger.info(f"Async Execution ID: {task_id}, Task ID: {task_id}")
        
        return ok({
            "task_id": task_id,
            "status": "queued",
            "message": "Pipeline execution submitted to Ray"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit pipeline execution: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Failed to submit pipeline execution: {str(e)}")
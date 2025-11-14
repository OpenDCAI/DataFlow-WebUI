from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.services.task_registry import TaskRegistry, _TASK_REGISTRY
from app.api.v1.envelope import ApiResponse
from app.api.v1.resp import ok, created
from app.api.v1.errors import *

router = APIRouter(tags=["tasks"])
_registry = _TASK_REGISTRY


@router.get("/", response_model=ApiResponse[List[TaskOut]], operation_id="list_tasks", summary="列出所有任务，支持按状态和执行器类型过滤")
def list_tasks(
    status: Optional[str] = Query(None, description="过滤状态: pending/running/success/failed/cancelled"),
    executor_type: Optional[str] = Query(None, description="过滤执行器类型: operator/pipeline")
):
    """
    列出所有任务，支持按状态和执行器类型过滤
    """
    tasks = _registry.list(status=status, executor_type=executor_type)
    return ok(tasks)


@router.post("/", response_model=ApiResponse[TaskOut], operation_id="create_task", summary="创建新任务")
def create_task(payload: TaskCreate):
    """
    创建新任务
    """
    try:
        task = _registry.create(payload.model_dump(mode="json"))
        return created(task)
    except Exception as e:
        raise HTTPException(400, f"Failed to create task: {e}")


@router.get("/statistics", response_model=ApiResponse[Dict], operation_id="get_task_statistics", summary="获取任务统计信息")
def get_task_statistics():
    """
    获取任务统计信息
    """
    stats = _registry.get_statistics()
    return ok(stats)


@router.get("/{task_id}", response_model=ApiResponse[TaskOut], operation_id="get_task", summary="获取指定任务详情")
def get_task(task_id: str):
    """
    获取指定任务详情
    """
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return ok(task)


@router.patch("/{task_id}", response_model=ApiResponse[TaskOut], operation_id="update_task", summary="更新任务状态和信息")
def update_task(task_id: str, payload: TaskUpdate):
    """
    更新任务状态和信息
    """
    # 过滤掉None值
    updates = {k: v for k, v in payload.model_dump(mode="json").items() if v is not None}
    
    if not updates:
        raise HTTPException(400, "No updates provided")
    
    task = _registry.update(task_id, updates)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    
    return ok(task)


@router.delete("/{task_id}", response_model=ApiResponse[Dict], operation_id="delete_task", summary="删除任务")
def delete_task(task_id: str):
    """
    删除任务
    """
    success = _registry.delete(task_id)
    if not success:
        raise HTTPException(404, f"Task {task_id} not found")
    return ok({"detail": f"Task {task_id} deleted successfully"})


@router.post("/{task_id}/start", response_model=ApiResponse[TaskOut], operation_id="start_task", summary="启动任务（将状态设为running）")
def start_task(task_id: str):
    """
    启动任务（将状态设为running）
    """
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    
    if task["status"] != "pending":
        raise HTTPException(400, f"Task {task_id} is not in pending state (current: {task['status']})")
    
    updated_task = _registry.update(task_id, {"status": "running"})
    return ok(updated_task)


@router.post("/{task_id}/complete", response_model=ApiResponse[TaskOut], operation_id="complete_task", summary="完成任务（将状态设为success）")
def complete_task(task_id: str, output_id: Optional[str] = None):
    """
    完成任务（将状态设为success）
    """
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    
    if task["status"] not in ["pending", "running"]:
        raise HTTPException(400, f"Cannot complete task in {task['status']} state")
    
    updates = {"status": "success"}
    if output_id:
        updates["output_id"] = output_id
    
    updated_task = _registry.update(task_id, updates)
    return ok(updated_task)


@router.post("/{task_id}/fail", response_model=ApiResponse[TaskOut], operation_id="fail_task", summary="标记任务失败")
def fail_task(task_id: str, error_message: Optional[str] = None):
    """
    标记任务失败
    """
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    
    if task["status"] not in ["pending", "running"]:
        raise HTTPException(400, f"Cannot fail task in {task['status']} state")
    
    updates = {"status": "failed"}
    if error_message:
        updates["error_message"] = error_message
    
    updated_task = _registry.update(task_id, updates)
    return ok(updated_task)


@router.post("/{task_id}/cancel", response_model=ApiResponse[TaskOut], operation_id="cancel_task", summary="取消任务")
def cancel_task(task_id: str):
    """
    取消任务
    """
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    
    if task["status"] not in ["pending", "running"]:
        raise HTTPException(400, f"Cannot cancel task in {task['status']} state")
    
    updated_task = _registry.update(task_id, {"status": "cancelled"})
    return ok(updated_task)



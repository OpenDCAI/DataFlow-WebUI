from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.services.task_registry import TaskRegistry, _TASK_REGISTRY

router = APIRouter(tags=["tasks"])
_registry = _TASK_REGISTRY


@router.get("/", response_model=List[TaskOut])
def list_tasks(
    status: Optional[str] = Query(None, description="过滤状态: pending/running/success/failed/cancelled"),
    executor_type: Optional[str] = Query(None, description="过滤执行器类型: operator/pipeline")
):
    """
    列出所有任务，支持按状态和执行器类型过滤
    """
    try:
        tasks = _registry.list(status=status, executor_type=executor_type)
        return tasks
    except Exception as e:
        raise HTTPException(500, f"Failed to list tasks: {e}")


@router.post("/", response_model=TaskOut)
def create_task(payload: TaskCreate):
    """
    创建新任务
    """
    try:
        task = _registry.create(payload.model_dump(mode="json"))
        return task
    except Exception as e:
        raise HTTPException(400, f"Failed to create task: {e}")


@router.get("/statistics")
def get_task_statistics():
    """
    获取任务统计信息
    """
    try:
        stats = _registry.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(500, f"Failed to get statistics: {e}")


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    """
    获取指定任务详情
    """
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: str, payload: TaskUpdate):
    """
    更新任务状态和信息
    """
    try:
        # 过滤掉None值
        updates = {k: v for k, v in payload.model_dump(mode="json").items() if v is not None}
        
        if not updates:
            raise HTTPException(400, "No updates provided")
        
        task = _registry.update(task_id, updates)
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Failed to update task: {e}")


@router.delete("/{task_id}")
def delete_task(task_id: str):
    """
    删除任务
    """
    success = _registry.delete(task_id)
    if not success:
        raise HTTPException(404, f"Task {task_id} not found")
    return {"detail": f"Task {task_id} deleted successfully"}


@router.post("/{task_id}/start", response_model=TaskOut)
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
    return updated_task


@router.post("/{task_id}/complete", response_model=TaskOut)
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
    return updated_task


@router.post("/{task_id}/fail", response_model=TaskOut)
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
    return updated_task


@router.post("/{task_id}/cancel", response_model=TaskOut)
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
    return updated_task



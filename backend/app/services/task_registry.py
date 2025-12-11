import yaml
import os
import hashlib
import pandas
from typing import Dict, List, Optional
from app.core.config import settings

class TaskRegistry:
    """任务注册表，用于管理运行任务的生命周期"""
    
    def __init__(self, path: str | None = None):
        self.path = path or settings.TASK_REGISTRY
        self._ensure()
    
    def _ensure(self):
        """确保注册表文件存在"""
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                yaml.safe_dump({"tasks": {}}, f, allow_unicode=True)
    
    def _read(self) -> Dict:
        """读取注册表"""
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"tasks": {}}
    
    def _write(self, data: Dict):
        """写入注册表"""
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    
    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        timestamp = pandas.Timestamp.now().isoformat()
        random_str = os.urandom(8).hex()
        combined = f"{timestamp}-{random_str}"
        return hashlib.md5(combined.encode("utf-8")).hexdigest()[:12]
    
    def list(self, status: Optional[str] = None, executor_type: Optional[str] = None) -> List[Dict]:
        """
        列出所有任务，可选过滤条件
        
        Args:
            status: 过滤特定状态的任务
            executor_type: 过滤特定类型的执行器 (operator/pipeline)
        """
        tasks = list(self._read()["tasks"].values())
        
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        
        if executor_type:
            tasks = [t for t in tasks if t.get("executor_type") == executor_type]
        
        # 按创建时间倒序排列
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return tasks
    
    def create(self, task: Dict) -> Dict:
        """
        创建新任务
        
        Args:
            task: 任务信息字典
        
        Returns:
            创建的任务（包含生成的ID和时间戳）
        """
        data = self._read()
        
        # 生成任务ID
        task_id = self._generate_task_id()
        task["id"] = task_id
        task["status"] = "pending"  # 初始状态
        task["created_at"] = pandas.Timestamp.now().isoformat()
        task["started_at"] = None
        task["finished_at"] = None
        task["output_id"] = None
        task["error_message"] = None
        
        # 保存任务
        tasks = data.get("tasks", {})
        tasks[task_id] = task
        data["tasks"] = tasks
        self._write(data)
        
        return task
    
    def get(self, task_id: str) -> Dict | None:
        """获取指定任务"""
        return self._read()["tasks"].get(task_id)
    
    def update(self, task_id: str, updates: Dict) -> Dict | None:
        """
        更新任务信息
        
        Args:
            task_id: 任务ID
            updates: 要更新的字段
        
        Returns:
            更新后的任务，如果任务不存在返回None
        """
        data = self._read()
        tasks = data.get("tasks", {})
        
        if task_id not in tasks:
            return None
        
        task = tasks[task_id]
        
        # 更新字段
        for key, value in updates.items():
            if value is not None:  # 只更新非None的值
                task[key] = value
        
        # 自动设置时间戳
        if "status" in updates:
            if updates["status"] == "running" and not task.get("started_at"):
                task["started_at"] = pandas.Timestamp.now().isoformat()
            elif updates["status"] in ["success", "failed", "cancelled"]:
                if not task.get("finished_at"):
                    task["finished_at"] = pandas.Timestamp.now().isoformat()
        
        tasks[task_id] = task
        data["tasks"] = tasks
        self._write(data)
        
        return task
    
    def delete(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功删除
        """
        data = self._read()
        tasks = data.get("tasks", {})
        
        if task_id in tasks:
            del tasks[task_id]
            data["tasks"] = tasks
            self._write(data)
            return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        tasks = self.list()
        
        stats = {
            "total": len(tasks),
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "cancelled": 0,
            "by_executor_type": {
                "operator": 0,
                "pipeline": 0
            }
        }
        
        for task in tasks:
            status = task.get("status", "pending")
            stats[status] = stats.get(status, 0) + 1
            
            executor_type = task.get("executor_type", "")
            if executor_type in stats["by_executor_type"]:
                stats["by_executor_type"][executor_type] += 1
        
        return stats


# 全局单例
# _TASK_REGISTRY = TaskRegistry()


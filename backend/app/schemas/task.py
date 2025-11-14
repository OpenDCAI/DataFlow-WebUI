from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal
from datetime import datetime

class TaskCreate(BaseModel):
    """创建任务时的输入"""
    dataset_id: str = Field(..., description="输入数据集ID")
    executor_name: str = Field(..., description="执行的算子或pipeline名称")
    executor_type: Literal["operator", "pipeline"] = Field(..., description="执行类型: operator 或 pipeline")
    meta: Dict[str, str] = Field(default_factory=dict, description="额外的元数据信息")

class TaskUpdate(BaseModel):
    """更新任务状态"""
    status: Optional[Literal["pending", "running", "success", "failed", "cancelled"]] = None
    output_id: Optional[str] = Field(None, description="输出结果数据集ID")
    error_message: Optional[str] = Field(None, description="错误信息(如果失败)")
    meta: Optional[Dict[str, str]] = None

class TaskOut(BaseModel):
    """任务输出，包含完整信息"""
    id: str = Field(..., description="任务唯一ID")
    dataset_id: str = Field(..., description="输入数据集ID")
    executor_name: str = Field(..., description="执行的算子或pipeline名称")
    executor_type: Literal["operator", "pipeline"] = Field(..., description="执行类型")
    output_id: Optional[str] = Field(None, description="输出结果数据集ID")
    status: Literal["pending", "running", "success", "failed", "cancelled"] = Field(
        ..., description="任务状态"
    )
    error_message: Optional[str] = Field(None, description="错误信息")
    meta: Dict[str, str] = Field(default_factory=dict, description="元数据")
    created_at: str = Field(..., description="创建时间")
    started_at: Optional[str] = Field(None, description="开始时间")
    finished_at: Optional[str] = Field(None, description="完成时间")



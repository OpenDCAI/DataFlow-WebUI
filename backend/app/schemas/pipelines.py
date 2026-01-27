from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from app.schemas.operator import OperatorDetailSchema
from dataflow.utils.storage import FileStorage

class Pipeline(str, Enum):
    """Pipeline类型枚举"""
    undefined = "undefined"
    agentic_rag = "agentic_rag"
    chemistry = "chemistry"
    code = "code"
    conversation = "conversation"
    core_speech = "core_speech"
    db = "db"
    core_text = "core_text"
    core_vision = "core_vision"
    general_text = "general_text"
    knowledge_cleaning = "knowledge_cleaning"
    text2sql = "text2sql"
    reasoning = "reasoning"
    code_generation = "code_generation"
    translation = "translation"
    text_pt = "text_pt"
    text_sft = "text_sft"


class ExecutionStatus(str, Enum):
    """Pipeline执行状态枚举"""
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class PipelineOperator(BaseModel): # 画布上的pipeline类
    """Pipeline算子模型"""
    name: str = Field(..., description="算子名称")
    params: Any = Field(default_factory=dict, description="算子参数配置")
    location: tuple[float, float] = Field(default=(0, 0), description="算子在画布上的位置, 包含x和y两个坐标值")
    # @field_validator('name')
    # def validate_operator_name(cls, v: str) -> str:
    #     """验证算子名称格式"""
    #     if not v.replace('_', '').isalnum():
    #         raise ValueError('Operator name can only contain letters, numbers and underscores')
    #         # 后续可以补充从可用算子集中验证算子名称是否存在
    #     return v

class PipelineInputDataset(BaseModel):
    """Pipeline输入数据集模型"""
    id: str = Field(..., description="数据集ID")
    location: tuple[float, float] = Field(default=(0, 0), description="数据集在画布上的位置")

class PipelineConfig(BaseModel):
    """Pipeline配置模型"""
    file_path: str = Field(..., description="Pipeline文件路径")
    input_dataset: Union[str, PipelineInputDataset] = Field(..., description="输入数据集ID或配置")
    # 用 list 的顺序代表算子执行顺序
    operators: List[PipelineOperator] = Field(default_factory=list, description="算子执行序列")
    
    # @field_validator('operators')
    # def validate_operators(cls, v: List[PipelineOperator]) -> List[PipelineOperator]:
    #     """确保至少有一个算子"""
    #     if not v:
    #         raise ValueError('Pipeline must have at least one operator')
    #     return v


class PipelineIn(BaseModel):
    """创建/更新Pipeline的请求模型"""
    name: str = Field(..., description="Pipeline名称")
    config: PipelineConfig = Field(..., description="Pipeline详细配置")
    tags: List[str] = Field(default_factory=list, description="标签列表，用于分类和搜索")
    
class PipelineUpdateIn(BaseModel):
    """更新Pipeline的请求模型"""
    name: Optional[str] = Field(None, description="Pipeline名称")
    config: Optional[PipelineConfig] = Field(None, description="Pipeline详细配置")
    tags: Optional[List[str]] = Field(None, description="标签列表，用于分类和搜索")

class PipelineOut(BaseModel):
    """Pipeline响应模型, 包含完整信息"""
    id: str = Field(..., description="Pipeline唯一标识符")
    name: str = Field(..., description="Pipeline名称")
    config: PipelineConfig = Field(..., description="Pipeline配置")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    status: ExecutionStatus = Field(..., description="当前执行状态")
    
    class Config:
        from_attributes = True


class PipelineExecutionRequest(BaseModel):
    """Pipeline执行请求模型"""
    pipeline_id: Optional[str] = Field(None, description="预定义Pipeline ID")
    config: Optional[PipelineConfig] = Field(None, description="自定义Pipeline配置")
    
    # @field_validator('pipeline_id', 'config')
    # def validate_at_least_one(cls, v, info):
    #     """确保至少提供pipeline_id或config之一"""
    #     if info.data.get('pipeline_id') is None and info.data.get('config') is None:
    #         raise ValueError('Either pipeline_id or config must be provided')
    #     return v


class PipelineExecutionResult(BaseModel):
    """Pipeline执行结果模型"""
    task_id: str = Field(..., description="执行会话唯一标识符")
    pipeline_id: Optional[str] = Field(None, description="Pipeline ID")
    pipeline_config: Optional[Dict[str, Any]] = Field(None, description="Pipeline配置快照")
    status: ExecutionStatus = Field(..., description="执行状态")
    output: Dict[str, Any] = Field(default_factory=dict, description="执行输出结果")
    logs: List[str] = Field(default_factory=list, description="执行日志列表")
    started_at: Optional[str] = Field(None, description="执行开始时间")
    completed_at: Optional[str] = Field(None, description="执行完成时间")
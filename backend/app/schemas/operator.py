from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class OperatorSchema(BaseModel):
    name: str
    type: Dict[str, str]
    allowed_prompts: Optional[List[str]] = []
    description: Optional[str] = None


class OperatorDetailOut(BaseModel):
    """算子详细信息输出模型"""
    node: int
    name: str
    description: str
    parameter: Dict[str, List[Dict[str, Any]]]  # {"init": [...], "run": [...]}
    required: str = ""
    depends_on: List[str] = []
    mode: str = ""
    path: str = ""
    operation_type: str = ""


class OperatorCategoryIn(BaseModel):
    """查询算子类别输入模型"""
    category: Optional[str] = Field(None, description="算子类别，如 text2sql, rag 等。为空则返回所有")


class OperatorSourceIn(BaseModel):
    """获取算子源码输入模型"""
    operator_name: str = Field(..., description="算子名称")


class OperatorSourceOut(BaseModel):
    """算子源码输出模型"""
    operator_name: str
    source_code: str


class OperatorPromptSourceIn(BaseModel):
    """获取算子 Prompt 模板源码输入模型"""
    operator_name: str = Field(..., description="算子名称")


class OperatorPromptSourceOut(BaseModel):
    """算子 Prompt 模板源码输出模型"""
    operator_name: str
    prompt_sources: Dict[str, str]  # {"PromptClassName": "source_code"}

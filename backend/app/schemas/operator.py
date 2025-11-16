from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

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


class OperatorRAGIn(BaseModel):
    """RAG 算子检索输入模型"""
    query: Union[str, List[str]] = Field(..., description="单个查询字符串或查询列表")
    category: Optional[str] = Field(None, description="算子类别，None 表示检索全部类别")
    top_k: int = Field(5, ge=1, le=20, description="返回 top-k 个结果")


class OperatorRAGOut(BaseModel):
    """RAG 算子检索输出模型"""
    query: Union[str, List[str]]
    results: Union[List[str], List[List[str]]]  # 单查询返回 List[str]，多查询返回 List[List[str]]


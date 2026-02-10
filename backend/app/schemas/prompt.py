from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict

class GetPromptSchema(BaseModel):
    #allowed_prompts: Optional[List[str]] = []
    allowed_prompts: Optional[Dict[str, str]] = Field(default_factory=dict)

class PromptSourceOut(BaseModel):
    name: str
    source: str

class OperatorPromptMapOut(BaseModel):
    operator_prompts: Dict[str, List[str]]

# 同OperatorDetailSchema，定义一个 Prompt 的详细信息
class PromptParameterSchema(BaseModel):
    name: str
    default_value: Any # 默认值可以是任何类型，所以用 Any
    kind: str # 例如 "POSITIONAL_OR_KEYWORD"

class PromptParameterGroupsSchema(BaseModel):
    init: List[PromptParameterSchema]
    build_prompt: List[PromptParameterSchema]


class PromptInfoOut(BaseModel):
    operator: List[str]
    class_str: str
    primary_type: str
    secondary_type: str
    description: str
    parameter: PromptParameterGroupsSchema

class PromptInfoMapOut(BaseModel):
    prompts: Dict[str, PromptInfoOut]
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


# ── User-defined prompt templates ────────────────────────────────────────────
# 用户自定义的 prompt 模板（本地保存）。底层在运行时实例化为 FormatStrPrompt
# 或自定义 PromptABC 子类，供算子调用。

class UserPromptTemplateBase(BaseModel):
    name: str
    description: Optional[str] = ""
    # f-string 风格模板，例如 "Given {question}, produce an answer."
    # 占位符名必须与运行时传入的列名一致。
    template: str
    # 允许使用此模板的算子名称（可为空，代表对所有算子都可选）。
    allowed_operators: List[str] = Field(default_factory=list)
    # 样例渲染时的占位符 → 示例值映射
    example_variables: Dict[str, Any] = Field(default_factory=dict)


class UserPromptTemplateCreate(UserPromptTemplateBase):
    pass


class UserPromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    allowed_operators: Optional[List[str]] = None
    example_variables: Optional[Dict[str, Any]] = None


class UserPromptTemplateOut(UserPromptTemplateBase):
    id: str
    created_at: str
    updated_at: str


class RenderPreviewIn(BaseModel):
    template: str
    variables: Dict[str, Any] = Field(default_factory=dict)


class RenderPreviewOut(BaseModel):
    rendered: str
    placeholders: List[str]
    missing: List[str]
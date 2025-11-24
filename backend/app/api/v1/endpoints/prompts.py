
from fastapi import APIRouter, HTTPException
from app.schemas.prompt import GetPromptSchema, PromptSourceOut, OperatorPromptMapOut, PromptInfoMapOut
from app.services.prompt_registry import _PROMPT_REGISTRY
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

router = APIRouter(tags=["prompts"])

@router.get(
    "/operator-mapping",
    response_model=ApiResponse[OperatorPromptMapOut],
    summary="查看所有算子及其对应的 Prompt 列表"
)
def get_operator_prompt_mapping():
    result = _PROMPT_REGISTRY.list_operator_prompts()
    return ok(result)

@router.get(
    "/prompt-info",
    response_model=ApiResponse[PromptInfoMapOut],
    summary="查看所有 prompt 的信息（operator, class string, category）"
)
def get_prompt_info():
    return ok(_PROMPT_REGISTRY.list_prompt_info())

@router.get(
    "/{operator_name}",
    response_model=ApiResponse[GetPromptSchema],
    summary="根据算子名称获取对应的 Prompt 列表"
)
def get_prompts(operator_name: str):
    result = _PROMPT_REGISTRY.get_prompts(operator_name)
    if not result:
        raise HTTPException(404, "Operator not found")
    return ok(result)

@router.get(
    "/source/{prompt_name}",
    response_model=ApiResponse[PromptSourceOut],
    summary="根据 Prompt 名称返回 Prompt 类的源码"
)
def get_prompt_source(prompt_name: str):
    result = _PROMPT_REGISTRY.get_prompt_source(prompt_name)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return ok(result)

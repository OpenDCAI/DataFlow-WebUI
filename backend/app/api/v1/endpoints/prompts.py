from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.prompt import (
    GetPromptSchema, PromptSourceOut, OperatorPromptMapOut,
    PromptInfoMapOut, PromptInfoOut,
    UserPromptTemplateCreate, UserPromptTemplateUpdate, UserPromptTemplateOut,
    RenderPreviewIn, RenderPreviewOut,
)
from app.core.container import container
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

router = APIRouter(tags=["prompts"])


# ── User-defined prompt templates (CRUD) ─────────────────────────────────────
# 注：这些路由必须**放在** "/{operator_name}" 这类通配路由之前，
# 否则 "/user" 会被当成算子名匹配到下面的只读接口。

@router.get(
    "/user",
    response_model=ApiResponse[List[UserPromptTemplateOut]],
    summary="列出所有用户自定义 prompt 模板",
)
def list_user_prompts():
    items = container.user_prompt_registry.list_all()
    return ok([UserPromptTemplateOut(**i) for i in items])


@router.post(
    "/user",
    response_model=ApiResponse[UserPromptTemplateOut],
    summary="创建用户自定义 prompt 模板",
)
def create_user_prompt(body: UserPromptTemplateCreate):
    rec = container.user_prompt_registry.create(
        name=body.name,
        description=body.description or "",
        template=body.template,
        allowed_operators=body.allowed_operators,
        example_variables=body.example_variables,
    )
    return ok(UserPromptTemplateOut(**rec))


@router.get(
    "/user/{tpl_id}",
    response_model=ApiResponse[UserPromptTemplateOut],
    summary="根据 ID 获取用户自定义 prompt 模板",
)
def get_user_prompt(tpl_id: str):
    rec = container.user_prompt_registry.get(tpl_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Template {tpl_id} not found")
    return ok(UserPromptTemplateOut(**rec))


@router.put(
    "/user/{tpl_id}",
    response_model=ApiResponse[UserPromptTemplateOut],
    summary="更新用户自定义 prompt 模板",
)
def update_user_prompt(tpl_id: str, body: UserPromptTemplateUpdate):
    updated = container.user_prompt_registry.update(
        tpl_id, **body.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Template {tpl_id} not found")
    return ok(UserPromptTemplateOut(**updated))


@router.delete(
    "/user/{tpl_id}",
    response_model=ApiResponse[dict],
    summary="删除用户自定义 prompt 模板",
)
def delete_user_prompt(tpl_id: str):
    removed = container.user_prompt_registry.delete(tpl_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Template {tpl_id} not found")
    return ok({"deleted": True, "id": tpl_id})


@router.post(
    "/user/preview",
    response_model=ApiResponse[RenderPreviewOut],
    summary="预览 f-string 模板的渲染结果（不落盘）",
)
def preview_user_prompt(body: RenderPreviewIn):
    result = container.user_prompt_registry.preview(body.template, body.variables)
    return ok(RenderPreviewOut(**result))


# ── Built-in prompts (read-only browsing) ────────────────────────────────────

@router.get(
    "/operator-mapping",
    response_model=ApiResponse[OperatorPromptMapOut],
    summary="查看所有算子及其对应的 Prompt 列表"
)
def get_operator_prompt_mapping():
    result = container.prompt_registry.list_operator_prompts()
    return ok(result)

@router.get(
    "/prompt-info",
    response_model=ApiResponse[PromptInfoMapOut],
    summary="查看所有 prompt 的信息（operator, class string, category）"
)
def get_prompt_info():
    return ok(container.prompt_registry.list_prompt_info())

@router.get(
    "/prompt-info/{prompt_name}",
    response_model=ApiResponse[PromptInfoOut],
    summary="根据 Prompt 名称获取 Prompt 信息"
)
def get_prompt_info_by_name(prompt_name: str):
    info_map = container.prompt_registry.list_prompt_info().prompts
    if prompt_name not in info_map:
        raise HTTPException(404, f"Prompt '{prompt_name}' not found")
    return ok(info_map[prompt_name])

@router.get(
    "/{operator_name}",
    response_model=ApiResponse[GetPromptSchema],
    summary="根据算子名称获取对应的 Prompt 列表"
)
def get_prompts(operator_name: str):
    result = container.prompt_registry.get_prompts(operator_name)
    if not result:
        raise HTTPException(404, "Operator not found")
    return ok(result)

@router.get(
    "/source/{prompt_name}",
    response_model=ApiResponse[PromptSourceOut],
    summary="根据 Prompt 名称返回 Prompt 类的源码"
)
def get_prompt_source(prompt_name: str):
    result = container.prompt_registry.get_prompt_source(prompt_name)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return ok(result)

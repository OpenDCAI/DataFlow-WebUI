# app/api/v1/endpoints/operators.py

import json
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from loguru import logger as log

# --- 1. Import required Schemas and response wrappers ---
from app.schemas.operator import (
    OperatorSchema,
    OperatorDetailSchema,
    OperatorDetailsResponseSchema,
    OperatorCategoryRecommendationRequest,
    OperatorCategoryRecommendationSchema,
)
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse
from app.api.v1.errors import ValidationBizError

# --- 2. Import service layer ---
from app.services.operator_registry import OPS_JSON_PATH
from app.services.operator_category_guide import (
    build_category_response,
    recommend_categories,
    valid_categories,
)
from app.core.container import container

router = APIRouter(tags=["operators"])


def _build_operator_agent_tips(op: Dict[str, Any]) -> tuple[list[str], str | None, str]:
    op_name = op.get("name") or "unknown_operator"
    level_1 = ((op.get("type") or {}).get("level_1") or "unknown")
    parameter = op.get("parameter") or {}
    init_params = {item.get("name") for item in parameter.get("init", []) if item.get("name")}
    run_params = {item.get("name") for item in parameter.get("run", []) if item.get("name")}

    tips: list[str] = [
        "先确认这个算子是否真的属于你当前已选 category，再决定是否继续保留它。",
    ]
    if any(name in init_params for name in ("llm_serving", "embedding_serving")):
        tips.append("这是依赖 serving 的算子；先调用 list_serving，填真实 id，不要留空也不要写占位符。")
    if "prompt_template" in init_params:
        tips.append("如果需要 prompt_template，只能传类名字符串或包含 cls_name 的结构化对象；优先直接用 system_prompt。")
    if any(name in init_params for name in ("process_fn", "filter_rules")):
        tips.append("动态代码参数只接受 lambda/def 字符串、带 code 字段的对象，或这两种形式组成的列表。")
    if any(name in run_params for name in ("input_key", "input_keys")):
        tips.append("input_key/input_keys 必须来自 get_dataset_columns 或上游 output_key，不能依赖默认字段名。")
        tips.append("在 validate_pipeline_config 返回 missing_input_field 时，优先采用 suggested_fields / repair_hint 修正字段绑定，而不是继续扩展 category 查询。")
    if any(name in run_params for name in ("output_key", "output_meta_key")):
        tips.append("output_key/output_meta_key 会进入后续字段流；命名后先做 validate_pipeline_config 再提交。")

    field_hint = None
    if any(name in run_params for name in ("input_key", "input_keys")):
        field_hint = (
            "This operator's default input/output field names are only demo defaults. "
            "Compare them against the user's real dataset columns and override when needed."
        )

    context_hint = (
        f"This operator is from top-level category '{level_1}'. Keep MCP context small: "
        "inspect only a small candidate set, then validate and commit instead of browsing more categories."
    )
    return tips, field_hint, context_hint


@router.get(
    "/",
    response_model=ApiResponse[List[OperatorSchema]],
    operation_id="list_operators_all",
    summary=(
        "INTERNAL: Return ALL registered operators (full catalog). Used by "
        "the web UI's operator sidebar. NOT exposed via MCP — agents must "
        "use `list_operators` (the category-scoped variant) instead."
    ),
)
def list_operators_all(lang: str = "zh", category: str = None):
    """Return operators, optionally filtered by category.

    This is the legacy unrestricted route, kept for the frontend which
    renders the full operator palette. It is **intentionally not
    whitelisted in the MCP server** (see ``app.mcp_server`` include_operations)
    so agents cannot accidentally pull the 145-op catalog into context.
    """
    try:
        op_list = container.operator_registry.get_op_list(lang=lang)
        if category:
            op_list = [
                op for op in op_list
                if (op.get("type") or {}).get("level_1") == category
            ]
        return ok(op_list)
    except Exception as e:
        log.error(f"Failed to get operator list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/by_category",
    response_model=ApiResponse[List[OperatorSchema]],
    operation_id="list_operators",
    summary=(
        "Return registered operators within a SINGLE category. `category` "
        "is REQUIRED. This is the agent-facing variant exposed via MCP."
    ),
)
def list_operators(
    category: str = Query(
        None,
        description=(
            "REQUIRED. One of the level_1 categories returned by "
            "list_operator_categories (e.g. 'core_text', 'general_text', "
            "'reasoning'). Calling this endpoint without a category — or "
            "with 'all' / 'unknown' — is rejected with a structured error "
            "so the agent can recover without wasting context on the full "
            "~145-operator catalog."
        ),
    ),
    lang: str = "zh",
):
    """Return operators belonging to a single top-level category (agent path).

    Why a dedicated route: the frontend operator palette still needs the
    full catalog, so the old ``/`` path (now ``list_operators_all``) stays
    liberal and is hidden from MCP. This route is the one whitelisted in
    ``app.mcp_server``; when the agent forgets ``category``, the response
    itself carries the list of valid values plus a two-step recovery hint,
    so the next tool call can succeed without a round-trip to the user.
    """
    try:
        op_list = container.operator_registry.get_op_list(lang=lang)
        valids = valid_categories(op_list)

        if not category or category.strip().lower() in {"all", "*", "unknown", "any"}:
            raise ValidationBizError(
                message=(
                    "list_operators requires a `category` argument. Returning the full "
                    "~145-operator catalog would overflow the agent context window. "
                    "Call list_operator_categories first, read use_for/not_for for each, "
                    "choose exactly one category, then re-invoke list_operators with it."
                ),
                code=40010,
                data={
                    "error": "category_required",
                    "valid_categories": valids,
                    "next_action": (
                        "Step 1: list_operator_categories  →  "
                        "Step 2: list_operators?category=<chosen>  →  "
                        "Step 3: get_operator_detail_by_name(name=<chosen op>)"
                    ),
                },
            )

        if category not in valids:
            # difflib hint for typos / hallucinated categories
            import difflib
            suggestions = difflib.get_close_matches(category, valids, n=3, cutoff=0.4)
            raise ValidationBizError(
                message=(
                    f"Category '{category}' does not exist. Pick exactly one of "
                    "valid_categories below. Do not invent category names."
                ),
                code=40011,
                data={
                    "error": "unknown_category",
                    "valid_categories": valids,
                    "did_you_mean": suggestions,
                },
            )

        filtered = [
            op for op in op_list
            if (op.get("type") or {}).get("level_1") == category
        ]
        return ok(filtered)
    except ValidationBizError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get operator list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/categories",
    response_model=ApiResponse[Dict[str, Dict[str, Any]]],
    operation_id="list_operator_categories",
    summary=(
        "Return mapping of operator top-level categories with count + "
        "use_for / not_for guidance + example operator names. "
        "ALWAYS call this BEFORE list_operators."
    ),
)
def list_operator_categories(lang: str = "zh"):
    """Cheap entry-point agents must call first.

    Each category in the response carries:
      - ``count``    : number of operators in this category
      - ``use_for``  : the data-engineering jobs this category is intended for
      - ``not_for``  : common mis-mappings (anti-patterns) to avoid
      - ``examples`` : 3-5 representative operator names

    The agent should read use_for/not_for, decide which single category
    matches the user's task, and then call ``list_operators?category=<X>``.
    """
    try:
        op_list = container.operator_registry.get_op_list(lang=lang)
        return ok(build_category_response(op_list))
    except Exception as e:
        log.error(f"Failed to get operator categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/details",
    response_model=ApiResponse[OperatorDetailsResponseSchema],
    operation_id="list_operators_details", 
    summary="Return all operator details (generated on first scan, then read from cache)"
)
def list_operators_details(lang: str = "zh"):
    """
    If cache file ops.json is missing, trigger operator scan and generate cache;
    If exists, read directly from cache and return detailed operator list.
    """
    try:
        ops_json_path = OPS_JSON_PATH.with_suffix(f'.{lang}.json')
        if not ops_json_path.exists():
            log.info("ops.json cache file not found, triggering automatic operator scan and generation...")
            ops_data = container.operator_registry.dump_ops_to_json(lang=lang)
        else:
            with open(ops_json_path, "r", encoding="utf-8") as f:
                ops_data = json.load(f)

        return ok(ops_data)
    except json.JSONDecodeError as e:
        log.error(f"ops.json file corrupted: {e}")
        raise HTTPException(status_code=500, detail=f"Cache file is corrupted: {e}")
    except Exception as e:
        log.error(f"Failed to get operator details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/details/{op_name}",
    response_model=ApiResponse[OperatorDetailSchema],
    operation_id="get_operator_detail_by_name",
    summary="Get single operator details by name",
)
def get_operator_detail_by_name(op_name: str, lang: str = "zh"):
    """Get detailed info for a single operator by name.

    Logic consistent with /details:
    - If cache not found, scan and generate ops.json;
    - Then match name in all buckets and return.
    """
    try:
        # Ensure cache exists
        ops_json_path = OPS_JSON_PATH.with_suffix(f'.{lang}.json')
        if not ops_json_path.exists():
            log.info("ops.json cache file not found, triggering automatic operator scan and generation...")
            ops_data = container.operator_registry.dump_ops_to_json(lang=lang)
        else:
            with open(ops_json_path, "r", encoding="utf-8") as f:
                ops_data = json.load(f)

        # Look up the operator in all buckets
        for bucket_name, items in ops_data.items():
            if not isinstance(items, list):
                continue
            for op in items:
                if not isinstance(op, dict):
                    continue
                if op.get("name") == op_name:
                    op_copy = dict(op)
                    agent_tips, field_hint, context_hint = _build_operator_agent_tips(op_copy)
                    op_copy["agent_tips"] = agent_tips
                    op_copy["field_binding_hint"] = field_hint
                    op_copy["mcp_context_hint"] = context_hint
                    return ok(op_copy)

        # Not found
        raise HTTPException(status_code=404, detail=f"Operator '{op_name}' not found")

    except json.JSONDecodeError as e:
        log.error(f"ops.json file corrupted: {e}")
        raise HTTPException(status_code=500, detail=f"Cache file is corrupted: {e}")
    except HTTPException:
        # Pass through the 404 above
        raise
    except Exception as e:
        log.error(f"Failed to get operator details (single): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/recommend_categories",
    response_model=ApiResponse[OperatorCategoryRecommendationSchema],
    operation_id="recommend_operator_categories",
    summary=(
        "Recommend up to 2 top-level operator categories from the task description and dataset columns. "
        "Use this to avoid broad category browsing in MCP."
    ),
)
def recommend_operator_categories(payload: OperatorCategoryRecommendationRequest):
    try:
        recommendation = recommend_categories(
            task_description=payload.task_description,
            dataset_columns=payload.dataset_columns or [],
            max_categories=payload.max_categories,
        )
        return ok(recommendation)
    except Exception as e:
        log.error(f"Failed to recommend operator categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

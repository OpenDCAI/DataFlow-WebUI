# app/api/v1/endpoints/operators.py

import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any 
from loguru import logger as log

# --- 1. 导入所有需要的 Schema 和响应封装 ---
from app.schemas.operator import (
    OperatorSchema, 
    OperatorDetailSchema,
    OperatorDetailsResponseSchema 
)
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

# --- 2. 导入服务层 ---
from app.services.operator_registry import OPS_JSON_PATH
from app.core.container import container

router = APIRouter(tags=["operators"])

@router.get(
    "/", 
    response_model=ApiResponse[List[OperatorSchema]],
    operation_id="list_operators", 
    summary="Return list of registered operators (simplified)"
)
def list_operators():
    """Return all registered operators (simplified version)."""
    try:
        op_list = container.operator_registry.get_op_list()
        return ok(op_list)
    except Exception as e:
        log.error(f"Failed to get operator list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/details",
    response_model=ApiResponse[OperatorDetailsResponseSchema],
    operation_id="list_operators_details", 
    summary="Return all operator details (generated on first scan, then read from cache)"
)
def list_operators_details():
    """
    If cache file ops.json is missing, trigger operator scan and generate cache;
    If exists, read directly from cache and return detailed operator list.
    """
    try:
        if not OPS_JSON_PATH.exists():
            log.info("ops.json cache file not found, triggering automatic operator scan and generation...")
            ops_data = container.operator_registry.dump_ops_to_json()
        else:
            with open(OPS_JSON_PATH, "r", encoding="utf-8") as f:
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
def get_operator_detail_by_name(op_name: str):
    """Get detailed info for a single operator by name.

    Logic consistent with /details:
    - If cache not found, scan and generate ops.json;
    - Then match name in all buckets and return.
    """
    try:
        # Ensure cache exists
        if not OPS_JSON_PATH.exists():
            log.info("ops.json cache file not found, triggering automatic operator scan and generation...")
            ops_data = container.operator_registry.dump_ops_to_json()
        else:
            with open(OPS_JSON_PATH, "r", encoding="utf-8") as f:
                ops_data = json.load(f)

        # 在所有 bucket 中查找指定算子
        for bucket_name, items in ops_data.items():
            if not isinstance(items, list):
                continue
            for op in items:
                if not isinstance(op, dict):
                    continue
                if op.get("name") == op_name:
                    return ok(op)

        # 未找到
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
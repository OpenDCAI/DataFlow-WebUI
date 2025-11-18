# app/api/v1/endpoints/operators.py

import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any 
from loguru import logger as log

# --- 1. 导入所有需要的 Schema 和响应封装 ---
from app.schemas.operator import (
    OperatorSchema, 
    OperatorDetailsResponseSchema 
)
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

# --- 2. 导入服务层 ---
from app.services.operator_registry import _op_registry, OPS_JSON_PATH


router = APIRouter(tags=["operators"])

@router.get(
    "/", 
    response_model=ApiResponse[List[OperatorSchema]],
    operation_id="list_operators", 
    summary="返回注册算子列表 (简化版)"
)
def list_operators():
    """返回所有注册的算子列表（简化版）。"""
    try:
        op_list = _op_registry.get_op_list()
        return ok(op_list)
    except Exception as e:
        log.error(f"获取算子列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/details",
    response_model=ApiResponse[OperatorDetailsResponseSchema],
    operation_id="list_operators_details", 
    summary="返回所有算子详细信息 (从缓存读取)"
)
def list_operators_details():
    """
    从后端缓存的 ops.json 文件中读取详细的算子列表。
    """
    try:
        if not OPS_JSON_PATH.exists():
            log.warning(f"ops.json 缓存文件未找到, 请先调用 /refresh-cache")
            raise HTTPException(
                status_code=404, 
                detail="Cache file not found. Please run POST /refresh-cache first."
            )
            
        with open(OPS_JSON_PATH, "r", encoding="utf-8") as f:
            ops_data = json.load(f)
            
        return ok(ops_data)
        
    except json.JSONDecodeError as e:
        log.error(f"ops.json 文件已损坏: {e}")
        raise HTTPException(status_code=500, detail=f"Cache file is corrupted: {e}")
    except Exception as e:
        log.error(f"获取算子详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/refresh-cache", 
    response_model=ApiResponse[Dict[str, Any]], # <-- 这个接口返回简单消息，保持不变
    operation_id="refresh_operator_cache", 
    summary="刷新算子缓存 (写入 ops.json)"
)
def refresh_operator_cache():
    """手动触发服务端的算子扫描。"""
    try:
        all_ops_data = _op_registry.dump_ops_to_json()
        
        return ok({
            "message": "Cache refreshed successfully", 
            "total_operators": len(all_ops_data.get("Default", []))
        })
    except Exception as e:
        log.error(f"刷新缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {e}")
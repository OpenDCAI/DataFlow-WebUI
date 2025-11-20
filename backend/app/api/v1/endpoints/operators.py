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
    summary="返回所有算子详细信息 (首次扫描生成，其后从缓存读取)"
)
def list_operators_details():
    """
    如果缓存文件 ops.json 不存在，则执行一次算子扫描并生成缓存；
    如果已存在，则直接从缓存文件中读取并返回详细算子列表。
    """
    try:
        if not OPS_JSON_PATH.exists():
            log.info("ops.json 缓存文件未找到，自动触发一次算子扫描并生成缓存...")
            ops_data = _op_registry.dump_ops_to_json()
        else:
            with open(OPS_JSON_PATH, "r", encoding="utf-8") as f:
                ops_data = json.load(f)

        return ok(ops_data)
    except json.JSONDecodeError as e:
        log.error(f"ops.json 文件已损坏: {e}")
        raise HTTPException(status_code=500, detail=f"Cache file is corrupted: {e}")
    except Exception as e:
        log.error(f"获取算子详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
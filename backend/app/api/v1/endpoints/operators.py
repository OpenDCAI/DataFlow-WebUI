import os
from fastapi import APIRouter, HTTPException, Query
from app.schemas.operator import (
    OperatorSchema,
    OperatorDetailOut,
    OperatorCategoryIn,
    OperatorSourceIn,
    OperatorSourceOut,
    OperatorPromptSourceIn,
    OperatorPromptSourceOut,
    OperatorRAGIn,
    OperatorRAGOut,
)
from app.services.operator_registry import _op_registry
from app.services.operator_tools_service import _operator_tools_service
from typing import List, Optional, Union
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse

router = APIRouter(tags=["operators"])

# ============ 基础算子列表 API ============

@router.get("/", response_model=ApiResponse[List[OperatorSchema]], operation_id="list_operators", summary="返回目前所有注册的算子列表")
def list_operators():
    """返回所有注册的算子列表（简化版）"""
    try:
        registry = _op_registry
        return ok(registry.get_op_list())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 算子详细信息 API ============

@router.get("/details", response_model=ApiResponse[List[OperatorDetailOut]], operation_id="list_operators_details", summary="返回指定类别的算子详细信息列表，包含参数等")
def list_operators_details(category: Optional[str] = Query(None, description="算子类别，如 text2sql, rag 等。为空则返回所有")):
    """返回算子详细信息，包含参数、描述等"""
    try:
        details = _operator_tools_service.get_operator_content_list(category)
        return ok(details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get operator details: {e}")


@router.get("/details/{category}", response_model=ApiResponse[List[OperatorDetailOut]], operation_id="get_operators_by_category", summary="根据类别获取算子详细信息")
def get_operators_by_category(category: str):
    """根据类别获取算子详细信息"""
    try:
        details = _operator_tools_service.get_operator_content_list(category)
        if not details:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        return ok(details)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get operators: {e}")


# ============ 算子源码 API ============

@router.get("/source/{operator_name}", response_model=ApiResponse[OperatorSourceOut], operation_id="get_operator_source", summary="根据算子名称获取算子的 Python 源码")
def get_operator_source(operator_name: str):
    """获取指定算子的源码"""
    try:
        source_code = _operator_tools_service.get_operator_source_by_name(operator_name)
        
        # 检查是否是错误信息
        if source_code.startswith("#"):
            # 可能是错误或警告信息
            if "未找到算子" in source_code or "无法获取源码" in source_code:
                raise HTTPException(status_code=404, detail=source_code)
        
        result = OperatorSourceOut(
            operator_name=operator_name,
            source_code=source_code
        )
        return ok(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get operator source: {e}")


# ============ Prompt 模板源码 API ============

@router.get("/prompt-source/{operator_name}", response_model=ApiResponse[OperatorPromptSourceOut], operation_id="get_operator_prompt_source", summary="获取算子的 Prompt 模板源码（随机2个示例）")
def get_operator_prompt_source(operator_name: str):
    """获取算子使用的 Prompt 模板源码"""
    try:
        prompt_sources = _operator_tools_service.get_prompt_sources_of_operator(operator_name)
        
        result = OperatorPromptSourceOut(
            operator_name=operator_name,
            prompt_sources=prompt_sources
        )
        return ok(result)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prompt sources: {e}")


# ============ RAG 智能检索 API ============

@router.post("/recommend", response_model=ApiResponse[OperatorRAGOut], operation_id="recommend_operators", summary="基于 AI 语义检索推荐相关算子（RAG）")
def recommend_operators(payload: OperatorRAGIn):
    """
    使用 RAG（检索增强生成）技术，根据用户的自然语言描述推荐最相关的算子
    
    支持单个查询或批量查询：
    - 单查询：query = "我想清洗文本数据"
    - 批量查询：query = ["清洗数据", "生成SQL"]
    
    需要配置环境变量 DF_API_KEY
    """
    try:
        results = _operator_tools_service.get_operators_by_rag(
            search_queries=payload.query,
            category=payload.category,
            top_k=payload.top_k,
        )
        
        response = OperatorRAGOut(
            query=payload.query,
            results=results
        )
        return ok(response)
    except RuntimeError as e:
        # API Key 相关错误
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recommend operators: {e}")


# ============ 缓存管理 API ============

@router.post("/refresh-cache", response_model=ApiResponse[dict], operation_id="refresh_operator_cache", summary="刷新算子缓存，重新扫描 OPERATOR_REGISTRY 并生成 ops.json")
def refresh_operator_cache():
    """手动刷新算子缓存"""
    try:
        all_ops = _operator_tools_service.dump_all_ops_to_file()
        return ok({"message": "Cache refreshed successfully", "total_operators": len(all_ops.get("Default", []))})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {e}")


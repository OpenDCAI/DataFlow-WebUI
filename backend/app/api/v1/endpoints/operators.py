import os
from fastapi import APIRouter, HTTPException
from app.schemas.operator import OperatorSchema
from app.services.operator_registry import _op_registry
from typing import List
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

router = APIRouter(tags=["operators"])

@router.get("/", response_model=ApiResponse[List[OperatorSchema]], operation_id="list_operators")
def list_operators():
    try:
        registry = _op_registry
        return ok(registry.get_op_list())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


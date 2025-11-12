import os
from fastapi import APIRouter, HTTPException
from app.schemas.operator import OperatorSchema
from app.services.operator_registry import _op_registry
from typing import List

router = APIRouter(tags=["operators"])

@router.get("/", response_model=List[OperatorSchema])
def list_operators():
    try:
        registry = _op_registry
        return registry.get_op_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


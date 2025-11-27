import os
from typing import List, Dict, Any 
from fastapi import APIRouter, HTTPException
from app.services.prompt_registry import _PROMPT_REGISTRY
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

from app.schemas.serving import (
    ServingQuerySchema,
    ServingCreateSchema,
    ServingDetailSchema,
    ServingClassSchema,
    ServingResponseSchema,
    ServingTestSchema
)
from app.services.serving_registry import _SERVING_REGISTRY, SERVING_CLS_REGISTRY

router = APIRouter(tags=["serving"])

@router.get(
    "/",
    response_model=ApiResponse[List[ServingDetailSchema]],
)
def list_serving_instances():
    try:
        serving_list = _SERVING_REGISTRY._get_all()
        if not serving_list:
            result = []
        else:
            result = []
            for k, v in serving_list.items():
                v['id'] = k
                result.append(v)
        return ok(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/classes",
    response_model=ApiResponse[List[ServingClassSchema]],
    operation_id="list_serving_classes",
    summary="获取所有可用Serving类定义"
)
def list_serving_classes():
    """
    返回所有注册的 Serving 类及其初始化参数信息 (名称、类型、默认值)。
    """
    try:
        classes_info = _SERVING_REGISTRY.get_serving_classes()
        return ok(classes_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{id}",
    response_model=ApiResponse[ServingDetailSchema],
    operation_id="get_serving_detail",
    summary="获取指定 Serving 实例的详细信息"
)
def get_serving_detail(id: str):
    """
    根据 Serving 实例的 ID，获取其详细信息。
    """
    try:
        serving_data = _SERVING_REGISTRY._get(id)
        if not serving_data:
            raise HTTPException(status_code=404, detail=f"Serving instance with id {id} not found")
        return ok(serving_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post(
    "/",
    response_model=ApiResponse[ServingQuerySchema],
    operation_id="create_serving_instance",
    summary="创建新的 Serving 实例"
)
def create_serving_instance(
    name: str,
    cls_name: str,
    params: List[Dict[str, Any]],
):
    """
    创建一个新的 Serving 实例。
    """
    try:        
        new_id = _SERVING_REGISTRY._set(name, cls_name, params)
        return ok({
            'id': new_id
        })
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post(
    "/{id}/test",
    response_model=ApiResponse[ServingResponseSchema],
    operation_id="test_serving_instance",
    summary="测试指定 Serving 实例的响应"
)
def test_serving_instance(id: str, body: ServingTestSchema):
    """
    测试指定 Serving 实例的响应。
    """
    try:
        prompt: str = body.prompt or "Hello, which model are you?"
        serving_info = _SERVING_REGISTRY._get(id)
        params_dict = {}
        ## This part of code is only for APILLMServing_request
        for params in serving_info['params']:
            if params['name'] == 'key_name_of_api_key':
                os.environ['DF_API_KEY'] = params['default']
                params['default'] = 'DF_API_KEY'
            params_dict[params['name']] = params['default']
        serving_instance = SERVING_CLS_REGISTRY[serving_info['cls_name']](**params_dict)
        responses = serving_instance.generate_from_input([prompt])
        if not serving_instance:
            raise HTTPException(status_code=404, detail=f"Serving instance with id {id} not found")
        response = {
            'id': id,
            'name': serving_info['name'],
            'cls_name': serving_info['cls_name'],
            'response': responses[0]
        }
        return ok(response)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
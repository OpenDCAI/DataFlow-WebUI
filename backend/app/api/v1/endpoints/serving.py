import os
import copy
from typing import List, Dict, Any 
from fastapi import APIRouter, HTTPException
from app.core.container import container
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse

from app.schemas.serving import (
    ServingQuerySchema,
    ServingCreateSchema,
    ServingDetailSchema,
    ServingClassSchema,
    ServingResponseSchema,
    ServingTestSchema,
    ServingUpdateSchema
)
from app.services.serving_registry import SERVING_CLS_REGISTRY

router = APIRouter(tags=["serving"])

@router.get(
    "/",
    response_model=ApiResponse[List[ServingDetailSchema]],
)
def list_serving_instances():
    try:
        serving_list = container.serving_registry._get_all()
        if not serving_list:
            result = []
        else:
            result = []
            for k, v in serving_list.items():
                v_copy = copy.deepcopy(v)
                v_copy['id'] = k
                if v_copy.get('cls_name') == 'APILLMServing_request':
                    # Filter out key_name_of_api_key from response
                    v_copy['params'] = [p for p in v_copy.get('params', []) if p['name'] not in ['key_name_of_api_key', 'api_key']]
                result.append(v_copy)
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
        classes_info = copy.deepcopy(container.serving_registry.get_serving_classes())
        api_llm_info = [x for x in classes_info if x['cls_name'] == 'APILLMServing_request']
        for item in api_llm_info:
            item['params'] = [p for p in item['params'] if p['name'] != 'key_name_of_api_key']
            item['params'].append({
                "name": "api_key",
                "type": "str",
                "default_value": "",
                "required": True
            })
        return ok(api_llm_info)
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
        serving_data = container.serving_registry._get(id)
        print(type(serving_data))
        if not serving_data:
            raise HTTPException(status_code=404, detail=f"Serving instance with id {id} not found")
        
        resp_data = copy.deepcopy(serving_data)
        if resp_data.get('cls_name') == 'APILLMServing_request':
             # Filter out key_name_of_api_key from response
            resp_data['params'] = [p for p in resp_data.get('params', []) if p['name'] not in ['key_name_of_api_key', 'api_key']]
            
        return ok(resp_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put(
    "/{id}",
    response_model=ApiResponse[ServingQuerySchema],
    operation_id="update_serving_instance",
    summary="更新 Serving 实例"
)
def update_serving_instance(id: str, body: ServingUpdateSchema):
    """
    更新 Serving 实例的配置。
    """
    try:
        params_list = None
        if body.params is not None:
            params_list = []
            for p in body.params:
                p_dict = p.model_dump(exclude_unset=True)
                # Map api_key back to key_name_of_api_key logic NOT needed here 
                # because we store api_key separately now.
                # Just ensure we are passing 'value' if present to update logic
                
                # However, the schema uses 'default_value' for storage in the registry mainly.
                # But the user request says frontend sends 'name' and 'value'
                # The schema update added 'value'.
                
                params_list.append(p_dict)
            
        success = container.serving_registry._update(
            id, 
            name=body.name, 
            params=params_list
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"Serving instance with id {id} not found")
            
        return ok({'id': id})
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(    e))

@router.delete(
    "/{id}",
    response_model=ApiResponse[ServingQuerySchema],
    operation_id="delete_serving_instance",
    summary="删除 Serving 实例"
)
def delete_serving_instance(id: str):
    """
    删除指定的 Serving 实例。
    """
    try:
        success = container.serving_registry._delete(id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Serving instance with id {id} not found")
        return ok({'id': id})
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
        # Get class default params info
        cls_info = None
        all_classes = container.serving_registry.get_serving_classes()
        for c in all_classes:
            if c['cls_name'] == cls_name:
                cls_info = c
                break
        
        if not cls_info:
             raise HTTPException(status_code=404, detail=f"Serving class {cls_name} not found")
             
        # Prepare base params from class definition
        # Use deepcopy to ensure we don't modify the original registry data structure accidentally
        final_params_map = {p['name']: copy.deepcopy(p) for p in cls_info['params']}
        
        # Merge User Params
        for user_p in params:
            pname = user_p['name']
            
            # Special validation for APILLMServing_request
            if cls_name == 'APILLMServing_request' and name == 'key_name_of_api_key':
                raise ValueError("key_name_of_api_key should not be provided in input")

            if pname in final_params_map:
                # Update existing param with user provided value
                if 'value' in user_p:
                    final_params_map[pname]['value'] = user_p['value']
            else:
                # New param (e.g. api_key)
                final_params_map[pname] = user_p

        new_params = list(final_params_map.values())

        new_id = container.serving_registry._set(name, cls_name, new_params)
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
        serving_info = container.serving_registry._get(id)
        params_dict = {}
        
        ## This part of code is only for APILLMServing_request
        if serving_info['cls_name'] == 'APILLMServing_request':
            api_key_val = None
            key_name_var = "DF_API_KEY"
            
            # First pass: find values
            for params in serving_info['params']:
                # Check 'value' first, then fallback to 'default_value'
                current_val = params.get('value') if params.get('value') is not None else params.get('default_value')
                
                if params['name'] == 'api_key':
                    api_key_val = current_val
                elif params['name'] == 'key_name_of_api_key':
                    key_name_var = current_val
            
            # Set env var if api_key is provided
            if api_key_val:
                os.environ[key_name_var] = api_key_val
                
            # Build params dict for init
            for params in serving_info['params']:
                if params['name'] != 'api_key':
                    params_dict[params['name']] = params.get('value') if params.get('value') is not None else params.get('default_value')
        else:
            for params in serving_info['params']:
                 params_dict[params['name']] = params.get('value') if params.get('value') is not None else params.get('default_value')

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
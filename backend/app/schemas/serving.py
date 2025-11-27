from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ServingQuerySchema(BaseModel):
    id: Optional[str] = Field(None, description="Serving实例的唯一标识符")

class ServingCreateSchema(BaseModel):
    name: str = Field(..., description="Serving实例的名称")
    cls_name: str = Field(..., description="Serving类的名称")
    params: Dict[str, Any] = Field(..., description="Serving实例的参数字典")

class ServingDetailSchema(ServingQuerySchema, ServingCreateSchema):
    pass

class ServingParamSchema(BaseModel):
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    default: Any = Field(None, description="默认值")
    required: bool = Field(True, description="是否必填")

class ServingClassSchema(BaseModel):
    cls_name: str = Field(..., description="Serving类名")
    params: List[ServingParamSchema] = Field(..., description="初始化参数列表")
    
class ServingResponseSchema(BaseModel):
    id: str = Field(..., description="Serving实例的唯一标识符")
    cls_name: str = Field(..., description="Serving类的名称")
    name: str = Field(..., description="Serving实例的名称")
    response: str = Field(..., description="响应结果")

class ServingTestSchema(BaseModel):
    prompt: Optional[str] = Field(None, description="测试用的 prompt")
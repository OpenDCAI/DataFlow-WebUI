from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True)
    code: int = Field(default=0, description="业务错误码，0 表示成功")
    message: str = Field(default="OK")
    data: Optional[T] = None
    meta: Optional[dict] = None  # 可放分页信息等

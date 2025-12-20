from pydantic import BaseModel, Field
from typing import Optional, List, Any


class Text2SQLDatabaseSchema(BaseModel):
    id: str = Field(..., description="text2sql database的标识符")
    name: Optional[str] = Field(None, description="database显示名称")
    file_name: Optional[str] = Field(None, description="上传文件名")
    uploaded_at: Optional[str] = Field(None, description="上传时间")
    size: Optional[int] = Field(None, description="文件大小")
    description: Optional[str] = Field(None, description="数据库描述")


class Text2SQLDatabaseManagerParamSchema(BaseModel):
    name: str = Field(..., description="参数名称")
    type: Optional[str] = Field(None, description="参数类型")
    default_value: Any = Field(None, description="默认值")
    value: Any = Field(None, description="参数值")
    required: Optional[bool] = Field(True, description="是否必填")


class Text2SQLDatabaseManagerQuerySchema(BaseModel):
    id: Optional[str] = Field(None, description="DatabaseManager 配置的唯一标识符")


class Text2SQLDatabaseManagerCreateSchema(BaseModel):
    name: str = Field(..., description="DatabaseManager配置名称")
    cls_name: str = Field("DatabaseManager", description="DatabaseManager类名")
    db_type: str = Field("sqlite", description="数据库类型")
    selected_db_ids: List[str] = Field(default_factory=list, description="选择的sqlite db_id列表")
    description: Optional[str] = Field(None, description="描述")


class Text2SQLDatabaseManagerUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="DatabaseManager配置名称")
    selected_db_ids: Optional[List[str]] = Field(None, description="选择的sqlite db_id列表")
    description: Optional[str] = Field(None, description="描述")


class Text2SQLDatabaseManagerDetailSchema(Text2SQLDatabaseManagerQuerySchema, Text2SQLDatabaseManagerCreateSchema):
    created_at: Optional[str] = Field(None, description="创建时间")


class Text2SQLDatabaseManagerClassSchema(BaseModel):
    cls_name: str = Field(..., description="DatabaseManager类名")
    params: List[Text2SQLDatabaseManagerParamSchema] = Field(..., description="初始化参数列表")



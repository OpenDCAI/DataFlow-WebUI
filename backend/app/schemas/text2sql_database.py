from pydantic import BaseModel, Field
from typing import Optional, List


class DatabaseSchema(BaseModel):
    id: str = Field(..., description="text2sql pipeline database 的标识符（db_id）")
    name: Optional[str] = Field(None, description="database 显示名称")
    file_name: Optional[str] = Field(None, description="上传文件名")
    uploaded_at: Optional[str] = Field(None, description="上传时间（ISO）")
    size: Optional[int] = Field(None, description="文件大小（bytes）")
    description: Optional[str] = Field(None, description="数据库描述")
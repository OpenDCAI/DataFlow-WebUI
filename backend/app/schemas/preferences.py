from pydantic import BaseModel, Field
from typing import Literal


class UserPreferences(BaseModel):
    """前端用户偏好配置（全局一份，直接覆盖）"""

    language: Literal["zh", "en"] = Field(
        "zh", description="界面语言，zh 或 en"
    )
    theme: Literal["light", "dark"] = Field(
        "light", description="主题模式，light(日间) 或 dark(夜间)"
    )




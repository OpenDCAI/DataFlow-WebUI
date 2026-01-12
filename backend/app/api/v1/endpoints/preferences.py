import json
import os
from fastapi import APIRouter, HTTPException

from app.api.v1.envelope import ApiResponse
from app.api.v1.resp import ok
from app.core.config import settings
from app.schemas.preferences import UserPreferences

router = APIRouter(tags=["preferences"])

# 配置文件路径：backend/data/user_preferences.json
PREFERENCES_PATH = os.path.join(settings.BASE_DIR, "data", "user_preferences.json")


def _read_preferences() -> UserPreferences:
    """读取偏好配置，不存在则返回默认值"""
    try:
        if not os.path.exists(PREFERENCES_PATH):
            # 直接用默认配置
            return UserPreferences()

        with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return UserPreferences(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read preferences: {e}")


def _write_preferences(prefs: UserPreferences) -> None:
    """写入偏好配置，直接覆盖"""
    try:
        os.makedirs(os.path.dirname(PREFERENCES_PATH), exist_ok=True)
        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            json.dump(prefs.model_dump(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write preferences: {e}")


@router.get(
    "/",
    response_model=ApiResponse[UserPreferences],
    summary="获取当前全局用户偏好配置",
)
def get_preferences():
    """
    返回当前偏好配置；如果文件不存在，返回默认配置。
    """
    prefs = _read_preferences()
    return ok(prefs)


@router.post(
    "/",
    response_model=ApiResponse[UserPreferences],
    summary="更新全局用户偏好配置（直接覆盖）",
)
def set_preferences(body: UserPreferences):
    """
    写入偏好配置，直接覆盖原文件。
    """
    _write_preferences(body)
    return ok(body)




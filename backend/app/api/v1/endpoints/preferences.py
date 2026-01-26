import json
import os
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.api.v1.envelope import ApiResponse
from app.api.v1.resp import ok
from app.core.config import settings
from app.schemas.preferences import UserPreferences

router = APIRouter(tags=["preferences"])

def _read_preferences() -> Dict[str, Any]:
    """读取偏好配置，不存在则返回None"""
    try:
        if not os.path.exists(settings.PREFERENCES_PATH):
            return None

        with open(settings.PREFERENCES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read preferences: {e}")


def _write_preferences(prefs: Dict[str, Any]) -> None:
    """写入偏好配置，直接覆盖"""
    try:
        os.makedirs(os.path.dirname(settings.PREFERENCES_PATH), exist_ok=True)
        with open(settings.PREFERENCES_PATH, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write preferences: {e}")


@router.get(
    "/",
    response_model=ApiResponse[dict],
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
    response_model=ApiResponse[dict],
    summary="更新全局用户偏好配置（直接覆盖）",
)
def set_preferences(body: dict):
    """
    写入偏好配置，直接覆盖原文件。
    """
    _write_preferences(body)
    return ok(body)




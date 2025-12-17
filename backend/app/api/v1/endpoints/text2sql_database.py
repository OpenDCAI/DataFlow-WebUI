from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.core.container import container
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse
from app.schemas.text2sql_database import DatabaseSchema

router = APIRouter(tags=["text2sql_database"])


@router.get(
    "/",
    response_model=ApiResponse[List[DatabaseSchema]],
    operation_id="list_databases",
    summary="列出所有已上传的sqlite数据库",
)
def list_databases():
    try:
        items = container.text2sql_database_registry.list()
        sanitized = []
        for x in items:
            y = {k: v for k, v in x.items() if k != "path"}
            sanitized.append(y)
        return ok(sanitized)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{db_id}",
    response_model=ApiResponse[DatabaseSchema],
    operation_id="get_database_detail",
    summary="获取指定db详情",
)
def get_database_detail(db_id: str):
    try:
        item = container.text2sql_database_registry._get(db_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"database {db_id} not found")
        item = {k: v for k, v in item.items() if k != "path"}
        return ok(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/upload",
    response_model=ApiResponse[DatabaseSchema],
    operation_id="upload_sqlite_database",
    summary="上传一个sqlite数据库文件并注册",
)
async def upload_sqlite_database(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    description: str | None = Form(None),
):
    try:
        content = await file.read()
        db_id = container.text2sql_database_registry.upload_sqlite_file(
            filename=file.filename,
            file_bytes=content,
            name=name,
            description=description
        )
        return created({"id": db_id})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to upload database: {e}")


@router.delete(
    "/{db_id}",
    response_model=ApiResponse[DatabaseSchema],
    operation_id="delete_database",
    summary="删除数据库",
)
def delete_database(db_id: str):
    try:
        ok_ = container.text2sql_database_registry._delete(db_id, remove_files=True)
        if not ok_:
            raise HTTPException(status_code=404, detail=f"database {db_id} not found")
        return ok({"id": db_id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
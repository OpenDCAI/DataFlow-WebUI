import copy
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.core.container import container
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse
from app.schemas.text2sql_database import (
    Text2SQLDatabaseSchema,
    Text2SQLDatabaseManagerDetailSchema,
    Text2SQLDatabaseManagerCreateSchema,
    Text2SQLDatabaseManagerUpdateSchema,
    Text2SQLDatabaseManagerQuerySchema,
    Text2SQLDatabaseManagerClassSchema,
)

router = APIRouter(tags=["text2sql_database"])
manager_router = APIRouter(tags=["text2sql_database_manager"])


@router.get(
    "/",
    response_model=ApiResponse[List[Text2SQLDatabaseSchema]],
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
    response_model=ApiResponse[Text2SQLDatabaseSchema],
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
    response_model=ApiResponse[Text2SQLDatabaseSchema],
    operation_id="upload_sqlite_database",
    summary="上传一个sqlite数据库文件并注册",
)
async def upload_sqlite_database(
    file: UploadFile = File(...),
    description: str | None = Form(None),
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        content = await file.read()
        db_id = container.text2sql_database_registry.upload_sqlite_file(
            filename=file.filename,
            file_bytes=content,
            description=description
        )
        return created({"id": db_id})
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload database: {e}")


@router.delete(
    "/{db_id}",
    response_model=ApiResponse[Text2SQLDatabaseSchema],
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


@manager_router.get(
    "/",
    response_model=ApiResponse[List[Text2SQLDatabaseManagerDetailSchema]],
    operation_id="list_text2sql_database_managers",
    summary="列出所有DatabaseManager配置",
)
def list_database_managers():
    try:
        items = container.text2sql_database_manager_registry.list()
        return ok(items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@manager_router.get(
    "/classes",
    response_model=ApiResponse[List[Text2SQLDatabaseManagerClassSchema]],
    operation_id="list_text2sql_database_manager_classes",
    summary="获取所有可用DatabaseManager类定义",
)
def list_database_manager_classes():
    try:
        classes_info = container.text2sql_database_manager_registry.get_manager_classes()
        return ok(classes_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@manager_router.get(
    "/{mgr_id}",
    response_model=ApiResponse[Text2SQLDatabaseManagerDetailSchema],
    operation_id="get_text2sql_database_manager_detail",
    summary="获取指定DatabaseManager配置详情",
)
def get_database_manager_detail(mgr_id: str):
    try:
        item = container.text2sql_database_manager_registry._get(mgr_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"database manager {mgr_id} not found")
        return ok(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@manager_router.post(
    "/",
    response_model=ApiResponse[Text2SQLDatabaseManagerQuerySchema],
    operation_id="create_text2sql_database_manager",
    summary="创建新的DatabaseManager",
)
def create_database_manager(body: Text2SQLDatabaseManagerCreateSchema):
    try:
        # Validate selected db ids exist
        if body.selected_db_ids:
            existing = {x["id"] for x in container.text2sql_database_registry.list()}
            missing = [x for x in body.selected_db_ids if x not in existing]
            if missing:
                raise HTTPException(status_code=400, detail=f"Unknown db_id(s): {missing}")

        mgr_id = container.text2sql_database_manager_registry._set(
            name=body.name,
            cls_name=body.cls_name,
            db_type=body.db_type,
            selected_db_ids=copy.deepcopy(body.selected_db_ids),
            description=body.description,
        )
        return ok({"id": mgr_id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@manager_router.put(
    "/{mgr_id}",
    response_model=ApiResponse[Text2SQLDatabaseManagerQuerySchema],
    operation_id="update_text2sql_database_manager",
    summary="更新DatabaseManager",
)
def update_database_manager(mgr_id: str, body: Text2SQLDatabaseManagerUpdateSchema):
    try:
        if body.selected_db_ids is not None:
            existing = {x["id"] for x in container.text2sql_database_registry.list()}
            missing = [x for x in body.selected_db_ids if x not in existing]
            if missing:
                raise HTTPException(status_code=400, detail=f"Unknown db_id(s): {missing}")

        success = container.text2sql_database_manager_registry._update(
            mgr_id,
            name=body.name,
            selected_db_ids=copy.deepcopy(body.selected_db_ids) if body.selected_db_ids is not None else None,
            description=body.description,
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"database manager {mgr_id} not found")
        return ok({"id": mgr_id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@manager_router.delete(
    "/{mgr_id}",
    response_model=ApiResponse[Text2SQLDatabaseManagerQuerySchema],
    operation_id="delete_text2sql_database_manager",
    summary="删除DatabaseManager",
)
def delete_database_manager(mgr_id: str):
    try:
        success = container.text2sql_database_manager_registry._delete(mgr_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"database manager {mgr_id} not found")
        return ok({"id": mgr_id})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
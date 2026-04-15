from fastapi import APIRouter, HTTPException, status
from loguru import logger as log
from app.schemas.json_schema import JsonSchemaCreate, JsonSchemaUpdate, JsonSchemaOut
from app.services.json_schema_manager import JsonSchemaManager
from app.api.v1.resp import ok
from app.api.v1.envelope import ApiResponse
from typing import List


router = APIRouter(tags=["json_schemas"])
manager = JsonSchemaManager()


@router.post(
    "",
    response_model=ApiResponse[JsonSchemaOut],
    summary="创建新的 JSON Schema"
)
def create_schema(schema_in: JsonSchemaCreate):
    """Create a new JSON schema."""
    try:
        schema_out = manager.create(
            name=schema_in.name,
            description=schema_in.description or "",
            schema=schema_in.schema,
            example=schema_in.example or ""
        )
        return ok(JsonSchemaOut(**schema_out))
    except Exception as e:
        log.error(f"Failed to create schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    response_model=ApiResponse[List[JsonSchemaOut]],
    summary="获取所有 JSON Schemas"
)
def list_schemas():
    """List all JSON schemas."""
    try:
        schemas = manager.list_all()
        return ok([JsonSchemaOut(**s) for s in schemas])
    except Exception as e:
        log.error(f"Failed to list schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{schema_id}",
    response_model=ApiResponse[JsonSchemaOut],
    summary="根据 ID 获取 JSON Schema"
)
def get_schema(schema_id: str):
    """Get a schema by ID."""
    try:
        schema = manager.get(schema_id)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema {schema_id} not found"
            )
        return ok(JsonSchemaOut(**schema))
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get schema {schema_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{schema_id}",
    response_model=ApiResponse[JsonSchemaOut],
    summary="更新 JSON Schema"
)
def update_schema(schema_id: str, schema_update: JsonSchemaUpdate):
    """Update a schema by ID."""
    try:
        update_data = schema_update.dict(exclude_unset=True)
        schema = manager.update(schema_id, **update_data)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema {schema_id} not found"
            )
        return ok(JsonSchemaOut(**schema))
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to update schema {schema_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{schema_id}",
    response_model=ApiResponse[dict],
    summary="删除 JSON Schema"
)
def delete_schema(schema_id: str):
    """Delete a schema by ID."""
    try:
        success = manager.delete(schema_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema {schema_id} not found"
            )
        return ok({"deleted": True, "id": schema_id})
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to delete schema {schema_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

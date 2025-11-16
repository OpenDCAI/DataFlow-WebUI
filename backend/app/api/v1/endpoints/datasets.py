import os
from fastapi import APIRouter, HTTPException
from app.schemas.dataset import DatasetIn, DatasetOut
from app.services.dataset_registry import DatasetRegistry, _DATASET_REGISTRY
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse
from app.api.v1.errors import *


router = APIRouter(tags=["datasets"])
_registry = _DATASET_REGISTRY

@router.get("/", response_model=ApiResponse[list[DatasetOut]], operation_id="list_datasets", summary="返回目前所有注册的数据集列表，包含每个数据集的条目数和文件大小")
def list_datasets():
    """返回所有数据集列表，每个数据集包含条目数(num_samples)和文件大小(file_size)信息"""
    return ok(_registry.list())

@router.post("/", response_model=ApiResponse[DatasetOut], operation_id="register_dataset", summary="注册一个新的数据集或更新已有数据集的信息，根据路径作为唯一主键")
def register_dataset(payload: DatasetIn):
    try:
        ds = _registry.add_or_update(payload.model_dump(mode="json")) # to dict
    except Exception as e:
        raise HTTPException(400, f"Failed to register dataset: {e}")
    return created(ds)

@router.get("/{ds_id}", response_model=ApiResponse[DatasetOut], operation_id="get_dataset", summary="根据数据集 ID 获取数据集信息")
def get_dataset(ds_id: str):
    ds = _registry.get(ds_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    return ok(ds)

@router.delete("/{ds_id}", operation_id="delete_dataset", summary="根据数据集 ID 删除数据集")
def delete_dataset(ds_id: str):
    ds = _registry.get(ds_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    _registry.remove(ds_id)
    return ok(message="Dataset deleted")


# getting sample data for visualization
from app.services.visualize_dataset import VisualizeDatasetService
_visualize_service = VisualizeDatasetService()
@router.get("/pandas_type_sample/{ds_id}", operation_id="get_pandas_data", summary="获取指定数据集的 Pandas 类型样本数据,用于前端展示预览，可以通过start和end参数控制获取多少数据")
def get_pandas_data(ds_id: str, start: int = 0, end: int = 5):
    try:
        ds = _registry.get(ds_id)
        if not ds:
            raise HTTPException(404, "Dataset not found")
        return ok(_visualize_service.get_pandas_read_function(ds, start, end))
    except Exception as e:
        raise HTTPException(500, f"Failed to get pandas data: {e}")

# Get other data by file
from fastapi.responses import FileResponse
@router.get("/file_type_sample/{ds_id}", operation_id="get_file_type_data", summary="获取指定数据集的文件类型样本数据，用于前端展示下载，可以是图片、文本等")
def get_file_type_data(ds_id: str):
    try:
        ds = _registry.get(ds_id)
        if not ds:
            raise HTTPException(404, "Dataset not found")
        file_path, media_type = _visualize_service.get_other_visualization_data(ds)
    except Exception as e:
        raise HTTPException(500, f"Failed to get file type data: {e}")
    
    return FileResponse(
        file_path,
        filename=os.path.basename(file_path),
        media_type=media_type
    )
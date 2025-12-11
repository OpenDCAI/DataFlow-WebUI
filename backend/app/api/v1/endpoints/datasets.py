import os
from fastapi import APIRouter, HTTPException
from app.schemas.dataset import DatasetIn, DatasetOut
from app.core.container import container
from app.api.v1.resp import ok, created
from app.api.v1.envelope import ApiResponse
from app.api.v1.errors import *


router = APIRouter(tags=["datasets"])

@router.get("/", response_model=ApiResponse[list[DatasetOut]], operation_id="list_datasets", summary="返回目前所有注册的数据集列表，包含每个数据集的条目数和文件大小")
def list_datasets():
    """返回所有数据集列表，每个数据集包含条目数(num_samples)和文件大小(file_size)信息"""
    return ok(container.dataset_registry.list())

@router.post("/", response_model=ApiResponse[DatasetOut], operation_id="register_dataset", summary="注册一个新的数据集或更新已有数据集的信息，根据路径作为唯一主键")
def register_dataset(payload: DatasetIn):
    try:
        ds = container.dataset_registry.add_or_update(payload.model_dump(mode="json")) # to dict
    except Exception as e:
        raise HTTPException(400, f"Failed to register dataset: {e}")
    return created(ds)

@router.get("/{ds_id}", response_model=ApiResponse[DatasetOut], operation_id="get_dataset", summary="根据数据集 ID 获取数据集信息")
def get_dataset(ds_id: str):
    ds = container.dataset_registry.get(ds_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    return ok(ds)

@router.delete("/{ds_id}", response_model=ApiResponse[dict], operation_id="delete_dataset", summary="根据数据集 ID 删除数据集")
def delete_dataset(ds_id: str):
    ds = container.dataset_registry.get(ds_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    container.dataset_registry.remove(ds_id)
    return ok(message="Dataset deleted")


# getting sample data for visualization
@router.get("/pandas_type_sample/{ds_id}", response_model=ApiResponse[str], operation_id="get_pandas_data", summary="获取指定数据集的 Pandas 类型样本数据,用于前端展示预览，可以通过start和end参数控制获取多少数据")
def get_pandas_data(ds_id: str, start: int = 0, end: int = 5):
    try:
        ds = container.dataset_registry.get(ds_id)
        if not ds:
            raise HTTPException(404, "Dataset not found")
        return ok(container.dataset_visualize_service.get_pandas_read_function(ds, start, end))
    except Exception as e:
        raise HTTPException(500, f"Failed to get pandas data: {e}")

# Get other data by file
from fastapi.responses import FileResponse
@router.get("/file_type_sample/{ds_id}", operation_id="get_file_type_data", summary="获取指定数据集的文件类型样本数据，用于前端展示下载，可以是图片、文本等")
def get_file_type_data(ds_id: str):
    try:
        ds = container.dataset_registry.get(ds_id)
        if not ds:
            raise HTTPException(404, "Dataset not found")
        file_path, media_type = container.dataset_visualize_service.get_other_visualization_data(ds)
    except Exception as e:
        raise HTTPException(500, f"Failed to get file type data: {e}")
    
    return FileResponse(
        file_path,
        filename=os.path.basename(file_path),
        media_type=media_type
    )

@router.get("/preview/{ds_id}", response_model=ApiResponse[list[dict]], operation_id="get_dataset_preview", summary="获取指定数据集的文件预览内容，支持json、jsonl和parquet格式")
def get_dataset_preview(ds_id: str, num_lines: int = 5):
    """获取指定数据集的文件预览内容，只支持json、jsonl和parquet格式
    
    Args:
        ds_id: 数据集ID
        num_lines: 要预览的行数，默认为5
        
    Returns:
        预览内容的列表，每个元素是一个字典
    """
    try:
        preview_data = container.dataset_registry.preview(ds_id, num_lines)
        return ok(preview_data)
    except FileNotFoundError:
        raise HTTPException(404, "Dataset not found")
    except Exception as e:
        raise HTTPException(500, f"Failed to get dataset preview: {e}")

@router.get("/columns/{ds_id}", response_model=ApiResponse[list[str]], operation_id="get_dataset_columns", summary="获取指定数据集的列名，支持json、jsonl和parquet格式")
def get_dataset_columns(ds_id: str):
    """获取指定数据集的列名，只支持json、jsonl和parquet格式
    
    Args:
        ds_id: 数据集ID
        
    Returns:
        列名列表，如果不支持则返回空列表
    """
    try:
        columns_data = container.dataset_registry.get_columns(ds_id)
        return ok(columns_data)
    except FileNotFoundError:
        raise HTTPException(404, "Dataset not found")
    except Exception as e:
        raise HTTPException(500, f"Failed to get dataset columns: {e}")
from fastapi import APIRouter, HTTPException
from app.schemas.dataset import DatasetIn, DatasetOut
from app.services.dataset_registry import DatasetRegistry

router = APIRouter(tags=["datasets"])
_registry = DatasetRegistry()

@router.get("/", response_model=list[DatasetOut])
def list_datasets():
    return _registry.list()

@router.post("/", response_model=DatasetOut)
def register_dataset(payload: DatasetIn):
    try:
        ds = _registry.add_or_update(payload.model_dump(mode="json")) # to dict
    except Exception as e:
        raise HTTPException(400, f"Failed to register dataset: {e}")
    return ds

@router.get("/{ds_id}", response_model=DatasetOut)
def get_dataset(ds_id: str):
    ds = _registry.get(ds_id)
    if not ds:
        raise HTTPException(404, "Dataset not found")
    return ds

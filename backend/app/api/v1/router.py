from fastapi import APIRouter
# from .endpoints import health, datasets, models, inference
from .endpoints import datasets
from .endpoints import operators
from .endpoints import tasks
from .endpoints import pipelines
api_router = APIRouter()
# api_router.include_router(health.router, prefix="/health")
api_router.include_router(datasets.router, prefix="/datasets")
api_router.include_router(operators.router, prefix="/operators")
api_router.include_router(tasks.router, prefix="/tasks")
api_router.include_router(pipelines.router, prefix="/pipelines")
# api_router.include_router(models.router, prefix="/models")
# api_router.include_router(inference.router, prefix="/inference")

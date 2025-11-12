from fastapi import FastAPI
from app.core.config import settings
from app.core.dataflow_setup import setup_dataflow_core
from app.api.v1.router import api_router as api_v1

def create_app() -> FastAPI:
    setup_dataflow_core()
    
    app = FastAPI(title="DataFlow Backend", version="1.0.0")
    app.include_router(api_v1, prefix="/api/v1")
    return app

app = create_app()

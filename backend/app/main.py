from fastapi import FastAPI
from app.core.config import settings
from app.core.dataflow_setup import setup_dataflow_core
from app.core.container import container
from app.api.v1.handlers import install_exception_handlers
from app.api.v1.router import api_router as api_v1

from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    setup_dataflow_core()
    container.init()
    app = FastAPI(title="DataFlow Backend", version="1.0.0")
    app.include_router(api_v1, prefix="/api/v1")
    app.add_middleware(
    CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_exception_handlers(app)
    return app

app = create_app()

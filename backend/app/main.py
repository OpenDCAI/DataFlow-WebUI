from fastapi import FastAPI
from app.core.config import settings
from app.core.logger_setup import logger
from app.core.dataflow_setup import setup_dataflow_core
from app.core.container import container
from app.api.v1.handlers import install_exception_handlers
from app.api.v1.router import api_router as api_v1

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.responses import Response
from pathlib import Path

app = FastAPI()

DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
INDEX_FILE = DIST_DIR / "index.html"


def create_app() -> FastAPI:
    setup_dataflow_core()
    container.init()
    app = FastAPI(title="DataFlow Backend", version="1.0.0")
    app.include_router(api_v1, prefix="/api/v1")
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    INDEX_FILE = DIST_DIR / "index.html"
    if not INDEX_FILE.exists():
        logger.warning("Warning: UI index file not found, please build the frontend first")
    else:
        app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="ui")
    install_exception_handlers(app)
    return app

app = create_app()

@app.get("/ui/{full_path:path}")
def spa_fallback(full_path: str):
    target = DIST_DIR / full_path
    if target.exists() and target.is_file():
        # 例如 /ui/assets/xxx.js 这种静态文件会被直接命中
        return FileResponse(target)
    return FileResponse(INDEX_FILE)
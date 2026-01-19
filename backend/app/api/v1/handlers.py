# app/api/handlers.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette import status
from app.api.v1.envelope import ApiResponse
from app.api.v1.errors import ApiError

def install_exception_handlers(app: FastAPI):

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        body = ApiResponse(
            success=False,
            code=exc.code,
            message=exc.message,
            data=exc.data,
            meta={"http_status": exc.http_status, "path": request.url.path},
        ).model_dump()
        # 关键：无论什么错误，都返回 200
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        body = ApiResponse(
            success=False,
            code=42200,
            message="Validation failed",
            data={"errors": exc.errors()},
            meta={"http_status": 422, "path": request.url.path},
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        body = ApiResponse(
            success=False,
            code=exc.status_code * 100,
            message=str(exc.detail) if exc.detail else "HTTP error",
            meta={"http_status": exc.status_code, "path": request.url.path},
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # 兜底：未知异常
        body = ApiResponse(
            success=False,
            code=50000,
            message="Internal error",
            meta={"http_status": 500, "path": request.url.path},
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)

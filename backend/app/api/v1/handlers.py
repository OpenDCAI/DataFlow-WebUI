# app/api/handlers.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette import status
from app.api.v1.envelope import ApiResponse
from app.api.v1.errors import ApiError


def _is_protocol_path(request: Request) -> bool:
    """MCP (and other non-/api/v1) transport paths speak their own wire
    protocol (e.g. JSON-RPC 2.0 over SSE). They must NOT be wrapped in the
    WebUI ApiResponse envelope, otherwise clients like Cursor reject the
    response with a JSON-RPC schema validation error."""
    return request.url.path.startswith("/mcp")


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
        if _is_protocol_path(request):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": jsonable_encoder(exc.errors())},
            )
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
        if _is_protocol_path(request):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None),
            )
        body = ApiResponse(
            success=False,
            code=exc.status_code * 100,
            message=str(exc.detail) if exc.detail else "HTTP error",
            meta={"http_status": exc.status_code, "path": request.url.path},
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        if _is_protocol_path(request):
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # 兜底：未知异常
        body = ApiResponse(
            success=False,
            code=50000,
            message="Internal error",
            meta={"http_status": 500, "path": request.url.path},
        ).model_dump()
        return JSONResponse(status_code=status.HTTP_200_OK, content=body)

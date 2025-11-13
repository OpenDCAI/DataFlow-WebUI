from fastapi import status
from fastapi.responses import JSONResponse
from .envelope import ApiResponse

def ok(data=None, message="OK", meta: dict | None = None):
    return ApiResponse(success=True, code=0, message=message, data=data, meta=meta)

def created(data=None, message="Created"):
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=ApiResponse(success=True, code=0, message=message, data=data).model_dump()
    )

def no_content():
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

from fastapi import status
from fastapi.responses import JSONResponse
from .envelope import ApiResponse

def ok(data=None, message="OK", meta: dict | None = {}):
    return ApiResponse(success=True, code=status.HTTP_200_OK, message=message, data=data, meta=meta)

def created(data=None, message="Created"):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiResponse(success=True, code=status.HTTP_200_OK, message=message, data=data).model_dump()
    )

def no_content():
    return JSONResponse(status_code=status.HTTP_200_OK, content=None)

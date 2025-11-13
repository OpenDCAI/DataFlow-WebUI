# app/api/errors.py
from fastapi import status

class ApiError(Exception):
    def __init__(self, message="Business error", *, code=1, http_status=status.HTTP_400_BAD_REQUEST, data=None):
        self.message = message
        self.code = code
        self.http_status = http_status  # 记录原本应当返回的 HTTP 状态码
        self.data = data

class NotFoundError(ApiError):
    def __init__(self, message="Not found", code=40401, data=None):
        super().__init__(message, code=code, http_status=status.HTTP_404_NOT_FOUND, data=data)

class ConflictError(ApiError):
    def __init__(self, message="Conflict", code=40901, data=None):
        super().__init__(message, code=code, http_status=status.HTTP_409_CONFLICT, data=data)

class ValidationBizError(ApiError):
    def __init__(self, message="Invalid request", code=40001, data=None):
        super().__init__(message, code=code, http_status=status.HTTP_400_BAD_REQUEST, data=data)

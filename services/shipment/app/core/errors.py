"""Business error hierarchy. Each class has an HTTP status and is returned as { code, message, details }."""
from typing import Any


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, *, code: str | None = None, details: Any = None):
        super().__init__(message)
        self.message = message
        self.details = details
        self.code = code or type(self).code

    def body(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class Unauthorized(AppError):
    status_code, code = 401, "UNAUTHORIZED"


class Forbidden(AppError):
    status_code, code = 403, "FORBIDDEN"


class NotFound(AppError):
    status_code, code = 404, "NOT_FOUND"


class Conflict(AppError):
    """State conflict or insufficient stock."""
    status_code, code = 409, "CONFLICT"


class UpstreamError(AppError):
    """A dependency returned an error or could not be reached."""
    status_code, code = 502, "UPSTREAM_ERROR"


class UpstreamTimeout(AppError):
    """A dependency did not answer in time."""
    status_code, code = 504, "UPSTREAM_TIMEOUT"

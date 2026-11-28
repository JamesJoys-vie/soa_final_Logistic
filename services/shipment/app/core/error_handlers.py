"""Turn every error into JSON in the shared { code, message, details } shape."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.errors import AppError

log = logging.getLogger("shipment.errors")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def on_app_error(_: Request, exc: AppError):
        return JSONResponse(exc.body(), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def on_validation_error(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(part) for part in error["loc"][1:]), "message": error["msg"]}
                   for error in exc.errors()]
        return JSONResponse({"code": "VALIDATION_ERROR", "message": "Dữ liệu không hợp lệ", "details": details},
                            status_code=400)

    @app.exception_handler(HTTPException)  # also covers the 404 / 405 raised by the router
    async def on_http_error(_: Request, exc: HTTPException):
        return JSONResponse({"code": f"HTTP_{exc.status_code}", "message": str(exc.detail), "details": None},
                            status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(Exception)
    async def on_unexpected(_: Request, exc: Exception):
        log.error("unhandled error", exc_info=exc)
        return JSONResponse({"code": "INTERNAL_ERROR", "message": "Lỗi hệ thống", "details": None}, status_code=500)

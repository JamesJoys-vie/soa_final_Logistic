"""X-Request-Id: created by the gateway, kept by Shipment and forwarded to Inventory to trace one flow."""
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def current_request_id() -> str:
    return _request_id.get()


@contextmanager
def request_id_scope(request_id: str | None = None) -> Iterator[str]:
    value = request_id or uuid.uuid4().hex
    token = _request_id.set(value)
    try:
        yield value
    finally:
        _request_id.reset(token)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        with request_id_scope(request.headers.get("X-Request-Id")) as request_id:
            response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

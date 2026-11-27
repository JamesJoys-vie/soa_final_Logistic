"""Base class for service-to-service clients: timeout, one retry, internal key, tracing, error mapping."""
import logging
import time
from typing import Any

import httpx

from app.core.errors import AppError, Conflict, UpstreamError, UpstreamTimeout
from app.core.metrics import Metrics
from app.core.request_context import current_request_id

log = logging.getLogger("shipment.clients")


class ServiceClient:
    target = "service"

    def __init__(self, http: httpx.Client, internal_api_key: str, metrics: Metrics, retry_delay_sec: float = 0.2):
        self._http = http
        self._internal_api_key = internal_api_key
        self._metrics = metrics
        self._retry_delay_sec = retry_delay_sec

    def close(self) -> None:
        self._http.close()

    def _post(self, path: str, payload: dict | None = None, *, ok_statuses: frozenset[int] = frozenset()) -> None:
        """At most two attempts. Retrying is safe because every internal API is idempotent."""
        try:
            self._post_once(path, payload, ok_statuses)
        except (UpstreamError, UpstreamTimeout) as first_error:
            log.warning("%s %s failed, retrying: %s", self.target, path, first_error.code)
            time.sleep(self._retry_delay_sec)
            try:
                self._post_once(path, payload, ok_statuses)
            except AppError as exc:
                if not isinstance(exc, Conflict):
                    self._metrics.upstream_failed(self.target)
                raise

    def _post_once(self, path: str, payload: dict | None, ok_statuses: frozenset[int]) -> None:
        headers = {"X-Internal-Key": self._internal_api_key, "X-Request-Id": current_request_id()}
        try:
            response = self._http.post(path, json=payload or {}, headers=headers)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeout(f"{self.target} phản hồi quá hạn", code=f"{self.target.upper()}_TIMEOUT",
                                  details={"path": path}) from exc
        except httpx.TransportError as exc:
            raise self._unavailable(path) from exc
        if response.status_code in ok_statuses:
            return
        if response.status_code == 409:  # a business answer, not an infrastructure failure: no retry
            body = self._error_body(response)
            raise Conflict(body.get("message", "Xung đột"), code=body.get("code"), details=body.get("details"))
        if not response.is_success:
            raise self._unavailable(path, response.status_code)

    def _unavailable(self, path: str, status: int | None = None) -> UpstreamError:
        return UpstreamError(f"Gọi {self.target} không thành công", code=f"{self.target.upper()}_ERROR",
                             details={"path": path, "status": status})

    @staticmethod
    def _error_body(response: httpx.Response) -> dict[str, Any]:
        """Error { code, message, details }; FastAPI's HTTPException wraps it in a "detail" key."""
        try:
            body = response.json()
        except ValueError:
            return {}
        if isinstance(body, dict) and isinstance(body.get("detail"), dict):
            body = body["detail"]
        return body if isinstance(body, dict) else {}

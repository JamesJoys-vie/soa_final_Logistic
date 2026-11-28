"""JSON logs with request_id for cross-service tracing."""
import json
import logging

from app.core.request_context import current_request_id


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"), "level": record.levelname, "service": "shipment",
            "logger": record.name, "request_id": current_request_id(), "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    for noisy in ("apscheduler", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

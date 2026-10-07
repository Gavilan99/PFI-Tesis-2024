import json
import logging
import sys
import uuid
from typing import Any

from flask import Flask, g, has_request_context, request


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = g.get("request_id") if has_request_context() else None
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "requestId": getattr(record, "request_id", None),
        }
        for key in ("method", "path", "status"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(app: Flask) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdFilter())

    level = app.config.get("LOG_LEVEL", "INFO")

    for logger_name in (None, "werkzeug", app.logger.name):
        target = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        target.handlers = [handler]
        target.setLevel(level)
        target.propagate = False

    # At DEBUG, botocore logs request parameters, a password among them. Never below WARNING.
    for noisy in ("boto3", "botocore", "urllib3", "s3transfer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    @app.before_request
    def assign_request_id() -> None:
        g.request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    @app.after_request
    def log_request(response):
        app.logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
            },
        )
        response.headers["X-Request-Id"] = g.get("request_id", "")
        return response

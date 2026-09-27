"""Logging configuration shared by the application and future workers."""

import json
import logging
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Render log records as compact JSON for machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        component = getattr(record, "component", None)
        if component:
            payload["component"] = component
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure structured application logs once at process startup."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True,
    )


def get_component_logger(component: str) -> logging.LoggerAdapter[logging.Logger]:
    """Return a logger adapter that tags records with a subsystem name."""
    return logging.LoggerAdapter(
        logging.getLogger("academic_services_platform"),
        {"component": component},
    )
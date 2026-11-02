"""
Structured logging configuration for the Ride Booking System.

Replaces ad-hoc ``print()`` calls with structured JSON logging via
Python's standard ``logging`` module with a JSON formatter.

Usage::

    from logging_config import setup_logging

    setup_logging()  # call once at startup

    import logging
    logger = logging.getLogger(__name__)
    logger.info("ride_requested", extra={"ride_id": 123, "user_id": 42})
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Output fields:
    - timestamp (ISO 8601 UTC)
    - level
    - logger (logger name)
    - message
    - module, funcName, lineno (source location)
    - Any extra fields passed via ``extra={}``

    This format is compatible with log aggregation tools (ELK, Loki,
    CloudWatch, etc.).
    """

    # Standard LogRecord attributes to exclude from extras
    _RESERVED = {
        "name", "msg", "args", "created", "relativeCreated",
        "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "filename", "module", "pathname", "levelno", "levelname",
        "thread", "threadName", "process", "processName",
        "msecs", "message", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Build base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add any extra fields passed via extra={}
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_logging(level: str | None = None) -> None:
    """Configure structured JSON logging for the application.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).
               Defaults to the ``LOG_LEVEL`` env var, or ``INFO``.
    """
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    # Remove any existing handlers on the root logger
    root = logging.getLogger()
    root.handlers.clear()

    # Create JSON handler writing to stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())

    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level, logging.INFO))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("confluent_kafka").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        "Structured logging initialized",
        extra={"log_level": log_level},
    )

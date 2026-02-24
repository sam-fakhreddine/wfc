"""Logging formatters for JSON and console output.

Provides SIEM-compatible JSON formatter and human-readable console formatter
with secret sanitization and request ID tracking.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from wfc.shared.logging.sanitizer import sanitize_message


class JSONFormatter(logging.Formatter):
    """SIEM-compatible JSON formatter with secret sanitization.

    Outputs structured JSON logs with:
    - ISO 8601 timestamps
    - Request ID (if available)
    - Code location (module, function, line)
    - Extra context fields
    - Secret sanitization

    Example output:
        {
            "timestamp": "2026-02-22T12:34:56.789Z",
            "level": "INFO",
            "logger": "wfc.api",
            "message": "Request processed",
            "request_id": "abc-123",
            "module": "routes",
            "function": "handle_request",
            "line_number": 42
        }
    """

    STANDARD_FIELDS = {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "exc_info",
        "exc_text",
        "stack_info",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_message(record.getMessage()),
            "module": record.module,
            "function": record.funcName if record.funcName else "<unknown>",
            "line_number": record.lineno,
        }

        if hasattr(record, "request_id") and record.request_id:
            log_data["request_id"] = record.request_id

        for key, value in record.__dict__.items():
            if key not in self.STANDARD_FIELDS and not key.startswith("_"):
                if isinstance(value, str):
                    log_data[key] = sanitize_message(value)
                else:
                    log_data[key] = value

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with color-coding.

    Provides:
    - Color-coded log levels
    - Compact single-line format
    - Human-readable timestamps
    - Secret sanitization

    Example output:
        [2026-02-22 12:34:56] INFO    wfc.api: Request processed
    """

    COLORS = {
        "DEBUG": "\033[0;36m",
        "INFO": "\033[0;32m",
        "WARNING": "\033[0;33m",
        "ERROR": "\033[0;31m",
        "CRITICAL": "\033[0;35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output.

        Args:
            record: The log record to format.

        Returns:
            Formatted log string with color codes.
        """
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        level_color = self.COLORS.get(record.levelname, "")
        level_name = record.levelname.ljust(8)

        message = sanitize_message(record.getMessage())

        formatted = f"[{timestamp}] {level_color}{level_name}{self.RESET} {record.name}: {message}"

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted

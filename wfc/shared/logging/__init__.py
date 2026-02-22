"""Centralized logging infrastructure for WFC.

This module provides structured logging with:
- Secret sanitization
- JSON and console formatters
- Request/session ID tracking
- Performance timing decorators
- Environment-based configuration
"""

import logging
import os

from wfc.shared.logging.config import LoggingConfig
from wfc.shared.logging.context import get_request_id
from wfc.shared.logging.formatters import ConsoleFormatter, JSONFormatter

__all__ = ["LoggingConfig", "get_logger"]


_logger_cache = {}


class RequestIDFilter(logging.Filter):
    """Filter that adds request_id to log records from context."""

    def filter(self, record):
        """Add request_id to the log record if available in context.

        Args:
            record: The log record to filter.

        Returns:
            True (always allow the record through).
        """
        request_id = get_request_id()
        if request_id:
            record.request_id = request_id
        return True


def get_logger(name: str) -> logging.Logger:
    """Get or create a configured logger.

    Creates a logger with the appropriate formatter (JSON or console) based on
    environment configuration. Loggers are cached and reused.

    Args:
        name: The logger name (will be prefixed with 'wfc.' if not already).

    Returns:
        Configured logger instance.

    Example:
        >>> logger = get_logger("api.routes")
        >>> logger.info("Request received")
    """
    use_centralized = os.getenv("USE_CENTRALIZED_LOGGING", "true").lower() == "true"

    if not use_centralized:
        return logging.getLogger(name)

    if not name.startswith("wfc."):
        name = f"wfc.{name}"

    if name in _logger_cache:
        return _logger_cache[name]

    config = LoggingConfig()

    logger = logging.getLogger(name)

    level = getattr(logging, config.log_level)
    logger.setLevel(level)

    logger.propagate = True

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)

        if config.log_format == "json":
            formatter = JSONFormatter()
        else:
            formatter = ConsoleFormatter()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.addFilter(RequestIDFilter())

    _logger_cache[name] = logger

    return logger

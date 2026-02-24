"""Request context middleware for logging.

Provides thread-safe and async-safe request ID tracking using contextvars.
"""

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Optional

_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context.

    Returns:
        Current request ID if set, None otherwise.
    """
    return _request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID in context.

    Args:
        request_id: The request ID to set.
    """
    _request_id_var.set(request_id)


def clear_request_id() -> None:
    """Clear the request ID from context."""
    _request_id_var.set(None)


@contextmanager
def request_context():
    """Context manager for request scope with automatic request_id generation.

    Generates a unique request ID (UUID v4) and stores it in context for the
    duration of the context manager. Automatically cleans up on exit.

    Yields:
        The generated request ID.

    Example:
        >>> with request_context() as request_id:
        ...     logger.info("Processing request")
        ...     # request_id is available in this scope
    """
    request_id = str(uuid.uuid4())

    previous_id = _request_id_var.get()

    try:
        _request_id_var.set(request_id)
        yield request_id
    finally:
        _request_id_var.set(previous_id)

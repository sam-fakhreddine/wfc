"""Logging decorators for performance and execution tracking.

Provides decorators for:
- Execution time logging
- Function entry/exit logging
- Performance monitoring
"""

import asyncio
import functools
import logging
import time
from typing import Callable, TypeVar

from wfc.shared.logging import get_logger

F = TypeVar("F", bound=Callable)


def log_execution_time(func: F = None, *, level: int = logging.DEBUG) -> F:
    """Decorator to log function execution time.

    Logs function entry and exit with execution duration in milliseconds.
    Supports both synchronous and asynchronous functions.

    Args:
        func: The function to decorate (when used without arguments).
        level: Log level to use (default: DEBUG).

    Returns:
        Decorated function.

    Example:
        >>> @log_execution_time
        ... def process_data():
        ...     # do work
        ...     pass

        >>> @log_execution_time(level=logging.INFO)
        ... def important_task():
        ...     # do work
        ...     pass

        >>> @log_execution_time
        ... async def async_task():
        ...     # do async work
        ...     pass
    """

    def decorator(f: F) -> F:
        @functools.wraps(f)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(f.__module__)
            logger.log(
                level,
                f"Executing {f.__name__}",
                extra={"func_name": f.__name__},
            )

            start_time = time.perf_counter()

            try:
                result = f(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.log(
                    level,
                    f"Completed {f.__name__} in {duration_ms:.2f}ms",
                    extra={
                        "func_name": f.__name__,
                        "duration_ms": duration_ms,
                    },
                )

        @functools.wraps(f)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(f.__module__)
            logger.log(
                level,
                f"Executing {f.__name__}",
                extra={"func_name": f.__name__},
            )

            start_time = time.perf_counter()

            try:
                result = await f(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.log(
                    level,
                    f"Completed {f.__name__} in {duration_ms:.2f}ms",
                    extra={
                        "func_name": f.__name__,
                        "duration_ms": duration_ms,
                    },
                )

        if asyncio.iscoroutinefunction(f):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    if func is None:
        return decorator
    else:
        return decorator(func)

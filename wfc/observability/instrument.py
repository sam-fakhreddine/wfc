"""
Instrumentation helpers.

Provides safe emit/metric functions that never raise.
All instrumentation code imports from here.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


def emit_event(
    event_type: str,
    source: str,
    payload: dict[str, Any] | None = None,
    level: str = "info",
) -> None:
    """Emit an observability event. Never raises."""
    try:
        from wfc.observability import get_bus, is_initialized
        from wfc.observability.events import ObservabilityEvent

        if not is_initialized():
            return

        bus = get_bus()
        session_id = _get_session_id()
        bus.emit(
            ObservabilityEvent(
                event_type=event_type,
                source=source,
                session_id=session_id,
                payload=payload or {},
                level=level,
            )
        )
    except Exception:
        logger.debug("Failed to emit event %s", event_type, exc_info=True)


def incr(name: str, value: int | float = 1, labels: dict[str, str] | None = None) -> None:
    """Increment a counter. Never raises."""
    try:
        from wfc.observability import get_registry, is_initialized

        if not is_initialized():
            return
        get_registry().counter(name).increment(value, labels=labels)
    except Exception:
        logger.debug("Failed to increment %s", name, exc_info=True)


def gauge_set(name: str, value: int | float, labels: dict[str, str] | None = None) -> None:
    """Set a gauge value. Never raises."""
    try:
        from wfc.observability import get_registry, is_initialized

        if not is_initialized():
            return
        get_registry().gauge(name).set(value, labels=labels)
    except Exception:
        logger.debug("Failed to set gauge %s", name, exc_info=True)


@contextmanager
def timed(name: str, labels: dict[str, str] | None = None):
    """Time a block and record as histogram. Never raises on entry/exit."""
    start = time.perf_counter()
    try:
        yield
    finally:
        try:
            elapsed = time.perf_counter() - start
            from wfc.observability import get_registry, is_initialized

            if is_initialized():
                get_registry().histogram(name).observe(elapsed, labels=labels)
        except Exception:
            logger.debug("Failed to record timing %s", name, exc_info=True)


def observe(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Record a histogram observation. Never raises."""
    try:
        from wfc.observability import get_registry, is_initialized

        if not is_initialized():
            return
        get_registry().histogram(name).observe(value, labels=labels)
    except Exception:
        logger.debug("Failed to observe %s", name, exc_info=True)


_cached_session_id: str = ""


def _get_session_id() -> str:
    global _cached_session_id
    if _cached_session_id:
        return _cached_session_id
    try:
        from wfc.observability import _lock as obs_lock

        with obs_lock:
            from wfc.observability import _provider_registry

            if _provider_registry is not None:
                from wfc.observability.config import ObservabilityConfig

                _cached_session_id = ObservabilityConfig.load().session_id
                return _cached_session_id
        return ""
    except Exception:
        return ""


def _reset_session_cache() -> None:
    """Reset cached session ID. For testing only."""
    global _cached_session_id
    _cached_session_id = ""

"""
WFC Observability — Loki Mode v0.1

Metrics collection, structured events, and provider plugin system.
Zero required dependencies. Lazy initialization.

Usage:
    from wfc.observability import get_registry, get_bus, get_provider_registry
    from wfc.observability import init, shutdown

    # Explicit init (or auto-inits on first get_*() call)
    init()

    # Use metrics
    registry = get_registry()
    counter = registry.counter("reviews.completed")
    counter.increment()

    # Emit events
    bus = get_bus()
    bus.emit(ObservabilityEvent(...))

    # Clean shutdown (also registered via atexit)
    shutdown()
"""

from __future__ import annotations

import atexit
import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .events import EventBus
    from .metrics import MetricsRegistry
    from .providers import ProviderRegistry

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_initialized = False
_registry: MetricsRegistry | None = None
_bus: EventBus | None = None
_provider_registry: ProviderRegistry | None = None
_shutdown_registered = False


def init(config_path: str | None = None) -> None:
    """
    Initialize the observability system.

    Loads config, creates singletons, registers providers, sets up atexit.
    Idempotent — safe to call multiple times.
    """
    global _initialized, _registry, _bus, _provider_registry, _shutdown_registered

    if _initialized:
        return

    with _lock:
        if _initialized:
            return

        try:
            from .config import ObservabilityConfig
            from .events import EventBus as _EventBus
            from .metrics import MetricsRegistry as _MetricsRegistry
            from .providers import ProviderRegistry as _ProviderRegistry

            config = ObservabilityConfig.load(config_path)

            _registry = _MetricsRegistry()
            _bus = _EventBus()
            _provider_registry = _ProviderRegistry()

            _provider_registry.register_from_config(config, _bus)

            if not _shutdown_registered:
                atexit.register(shutdown)
                _shutdown_registered = True

            _initialized = True
            logger.debug("Observability initialized (session=%s)", config.session_id)

        except Exception:
            logger.warning(
                "Failed to initialize observability — continuing without it", exc_info=True
            )


def shutdown() -> None:
    """
    Shutdown the observability system.

    Takes final snapshot, flushes and closes all providers.
    Idempotent — safe to call multiple times.
    """
    global _initialized, _registry, _bus, _provider_registry

    if not _initialized:
        return

    with _lock:
        if not _initialized:
            return

        try:
            if _registry and _provider_registry:
                snapshot = _registry.snapshot()
                _provider_registry.push_snapshot(snapshot)

            if _provider_registry:
                _provider_registry.flush_all()
                _provider_registry.close_all()

        except Exception:
            logger.warning("Error during observability shutdown", exc_info=True)
        finally:
            _initialized = False


def get_registry() -> MetricsRegistry:
    """Get the metrics registry. Auto-initializes if needed."""
    if not _initialized:
        init()
    if _registry is None:
        from .metrics import MetricsRegistry as _MetricsRegistry

        return _MetricsRegistry()
    return _registry


def get_bus() -> EventBus:
    """Get the event bus. Auto-initializes if needed."""
    if not _initialized:
        init()
    if _bus is None:
        from .events import EventBus as _EventBus

        return _EventBus()
    return _bus


def get_provider_registry() -> ProviderRegistry:
    """Get the provider registry. Auto-initializes if needed."""
    if not _initialized:
        init()
    if _provider_registry is None:
        from .providers import ProviderRegistry as _ProviderRegistry

        return _ProviderRegistry()
    return _provider_registry


def is_initialized() -> bool:
    """Check if observability is initialized."""
    return _initialized


def reset() -> None:
    """Reset all state. For testing only."""
    global _initialized, _registry, _bus, _provider_registry
    with _lock:
        if _provider_registry:
            try:
                _provider_registry.close_all()
            except Exception:
                logger.debug("Failed to close provider registry during reset", exc_info=True)
        if _registry:
            _registry.reset()
        _initialized = False
        _registry = None
        _bus = None
        _provider_registry = None

        try:
            from .instrument import _reset_session_cache

            _reset_session_cache()
        except Exception:
            logger.debug("Failed to reset session cache", exc_info=True)

"""
Provider plugin interface for observability.

ObservabilityProvider ABC and ProviderRegistry.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wfc.observability.config import ObservabilityConfig
    from wfc.observability.events import EventBus, ObservabilityEvent

logger = logging.getLogger(__name__)


class ObservabilityProvider(ABC):
    """Abstract base class for observability providers."""

    PROVIDER_API_VERSION = 1

    @abstractmethod
    def on_event(self, event: ObservabilityEvent) -> None:
        """Handle an observability event."""
        ...

    @abstractmethod
    def on_metric_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Handle a metrics snapshot."""
        ...

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered data."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the provider and release resources."""
        ...


class ProviderRegistry:
    """Manages registered providers."""

    def __init__(self):
        self._providers: list[ObservabilityProvider] = []

    @property
    def providers(self) -> list[ObservabilityProvider]:
        return list(self._providers)

    def register(self, provider: ObservabilityProvider) -> None:
        self._providers.append(provider)

    def unregister(self, provider: ObservabilityProvider) -> None:
        self._providers = [p for p in self._providers if p is not provider]

    def push_snapshot(self, snapshot: dict[str, Any]) -> None:
        for provider in self._providers:
            try:
                provider.on_metric_snapshot(snapshot)
            except Exception:
                logger.warning(
                    "Provider %s failed on snapshot", type(provider).__name__, exc_info=True
                )

    def flush_all(self) -> None:
        for provider in self._providers:
            try:
                provider.flush()
            except Exception:
                logger.warning(
                    "Provider %s failed on flush", type(provider).__name__, exc_info=True
                )

    def close_all(self) -> None:
        for provider in self._providers:
            try:
                provider.close()
            except Exception:
                logger.warning(
                    "Provider %s failed on close", type(provider).__name__, exc_info=True
                )

    def register_from_config(self, config: ObservabilityConfig, bus: EventBus) -> None:
        """Register providers based on config and wire them to the event bus."""
        for name in config.providers:
            try:
                provider = self._create_provider(name, config)
                self.register(provider)
                bus.register_provider(provider)
            except Exception:
                logger.warning("Failed to create provider '%s'", name, exc_info=True)

    def _create_provider(self, name: str, config: ObservabilityConfig) -> ObservabilityProvider:
        if name == "null":
            from .null_provider import NullProvider

            return NullProvider()
        elif name == "memory":
            from .memory_provider import InMemoryProvider

            return InMemoryProvider()
        elif name == "file":
            from .file_provider import FileProvider

            return FileProvider(
                output_dir=config.file_output_dir,
                session_id=config.session_id,
            )
        elif name == "console":
            from .console_provider import ConsoleProvider

            return ConsoleProvider(verbosity=config.console_verbosity)
        else:
            raise ValueError(f"Unknown provider: {name}")

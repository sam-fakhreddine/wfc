"""
Structured event emitter.

Simplified direct-dispatch model. No pub-sub, no wildcards.
Events are dispatched directly to registered providers.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class EventReceiver(Protocol):
    """Protocol for anything that can receive events (providers)."""

    def on_event(self, event: ObservabilityEvent) -> None:
        ...


@dataclass
class ObservabilityEvent:
    """Structured observability event."""

    event_type: str
    source: str
    session_id: str
    payload: dict[str, Any]
    level: str = "info"
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventBus:
    """
    Direct-dispatch event bus.

    Emits events to all registered providers. Provider errors are isolated.
    No wildcard matching, no subscribers, no async — simple and correct.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._providers: list[EventReceiver] = []

    def register_provider(self, provider: EventReceiver) -> None:
        with self._lock:
            self._providers.append(provider)

    def unregister_provider(self, provider: EventReceiver) -> None:
        with self._lock:
            self._providers = [p for p in self._providers if p is not provider]

    def emit(self, event: ObservabilityEvent) -> None:
        with self._lock:
            providers = list(self._providers)

        for provider in providers:
            try:
                provider.on_event(event)
            except Exception:
                logger.warning(
                    "Provider %s failed on event %s",
                    type(provider).__name__,
                    event.event_type,
                    exc_info=True,
                )

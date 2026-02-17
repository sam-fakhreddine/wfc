"""InMemoryProvider: stores events in a list for testing."""

from __future__ import annotations

from typing import Any

from wfc.observability.events import ObservabilityEvent

from . import ObservabilityProvider


class InMemoryProvider(ObservabilityProvider):
    """In-memory provider for testing. Stores events and snapshots in lists."""

    DEFAULT_MAX_EVENTS = 10000

    def __init__(self, max_events: int | None = None):
        self.max_events = max_events or self.DEFAULT_MAX_EVENTS
        self.events: list[ObservabilityEvent] = []
        self.snapshots: list[dict[str, Any]] = []

    def on_event(self, event: ObservabilityEvent) -> None:
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

    DEFAULT_MAX_SNAPSHOTS = 100

    def on_metric_snapshot(self, snapshot: dict[str, Any]) -> None:
        self.snapshots.append(snapshot)
        if len(self.snapshots) > self.DEFAULT_MAX_SNAPSHOTS:
            self.snapshots = self.snapshots[-self.DEFAULT_MAX_SNAPSHOTS :]

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def clear(self) -> None:
        """Clear all stored events and snapshots."""
        self.events.clear()
        self.snapshots.clear()

    def find(
        self,
        event_type: str | None = None,
        event_type_prefix: str | None = None,
    ) -> list[ObservabilityEvent]:
        """Query stored events."""
        results = self.events
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if event_type_prefix:
            results = [e for e in results if e.event_type.startswith(event_type_prefix)]
        return results

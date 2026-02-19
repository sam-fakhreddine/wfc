"""NullProvider: no-op default. Zero overhead."""

from __future__ import annotations

from typing import Any

from wfc.observability.events import ObservabilityEvent

from . import ObservabilityProvider


class NullProvider(ObservabilityProvider):
    """No-op provider. Used when no observability is configured."""

    def on_event(self, event: ObservabilityEvent) -> None:
        pass

    def on_metric_snapshot(self, snapshot: dict[str, Any]) -> None:
        pass

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

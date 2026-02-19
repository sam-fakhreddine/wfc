"""ConsoleProvider: pretty-prints events to stderr."""

from __future__ import annotations

import os
import sys
from typing import Any

from wfc.observability.events import ObservabilityEvent

from . import ObservabilityProvider

_LEVEL_PRIORITY = {"error": 0, "warning": 1, "info": 2, "debug": 3}


class ConsoleProvider(ObservabilityProvider):
    """Prints events to stderr with optional ANSI coloring."""

    def __init__(self, verbosity: int = 1):
        self._verbosity = verbosity
        self._use_color = os.environ.get("NO_COLOR") is None

    def on_event(self, event: ObservabilityEvent) -> None:
        level_priority = _LEVEL_PRIORITY.get(event.level, 2)
        if level_priority > self._verbosity:
            return

        msg = self._format_event(event)
        print(msg, file=sys.stderr)

    def on_metric_snapshot(self, snapshot: dict[str, Any]) -> None:
        pass

    def flush(self) -> None:
        sys.stderr.flush()

    def close(self) -> None:
        self.flush()

    def _format_event(self, event: ObservabilityEvent) -> str:
        ts = event.timestamp[:19] if len(event.timestamp) >= 19 else event.timestamp
        level = event.level.upper()
        parts = [f"[{ts}]", f"[{level}]", event.event_type, f"src={event.source}"]

        for key, value in event.payload.items():
            parts.append(f"{key}={value}")

        line = " ".join(parts)

        if self._use_color:
            color = self._level_color(event.level)
            return f"\033[{color}m{line}\033[0m"
        return line

    @staticmethod
    def _level_color(level: str) -> str:
        return {
            "error": "31",
            "warning": "33",
            "info": "36",
            "debug": "37",
        }.get(level, "0")

"""
Metrics collection layer.

Counter, Gauge, Histogram, Timer, and MetricsRegistry.
Thread-safe. Zero dependencies. Lazy-initialized.
"""

from __future__ import annotations

import statistics
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any


def _label_key(labels: dict[str, str] | None) -> str:
    """Convert labels dict to a hashable key."""
    if not labels:
        return ""
    return "|".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Counter:
    """Monotonically increasing counter."""

    def __init__(self, name: str):
        self.name = name
        self._lock = threading.Lock()
        self._values: dict[str, int | float] = {"": 0}

    def increment(self, value: int | float = 1, labels: dict[str, str] | None = None) -> None:
        if value < 0:
            raise ValueError("Counter increment must be non-negative")
        key = _label_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def get(self, labels: dict[str, str] | None = None) -> int | float:
        key = _label_key(labels)
        if key:
            with self._lock:
                return self._values.get(key, 0)
        with self._lock:
            return sum(self._values.values())

    def _snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "type": "counter",
                "value": sum(self._values.values()),
                "labels": {k: v for k, v in self._values.items() if k},
            }


class Gauge:
    """Arbitrary-value gauge."""

    def __init__(self, name: str):
        self.name = name
        self._lock = threading.Lock()
        self._values: dict[str, int | float] = {"": 0}

    def set(self, value: int | float, labels: dict[str, str] | None = None) -> None:
        key = _label_key(labels)
        with self._lock:
            self._values[key] = value

    def increment(self, value: int | float = 1, labels: dict[str, str] | None = None) -> None:
        key = _label_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def decrement(self, value: int | float = 1, labels: dict[str, str] | None = None) -> None:
        key = _label_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) - value

    def get(self, labels: dict[str, str] | None = None) -> int | float:
        key = _label_key(labels)
        with self._lock:
            return self._values.get(key, 0)

    def _snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name": self.name,
                "type": "gauge",
                "value": self._values.get("", 0),
                "labels": {k: v for k, v in self._values.items() if k},
            }


class Histogram:
    """Distribution of observed values with percentile support."""

    def __init__(self, name: str):
        self.name = name
        self._lock = threading.Lock()
        self._observations: dict[str, list[float]] = {"": []}

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        key = _label_key(labels)
        with self._lock:
            if key not in self._observations:
                self._observations[key] = []
            self._observations[key].append(value)

    def count(self, labels: dict[str, str] | None = None) -> int:
        key = _label_key(labels)
        if key:
            with self._lock:
                return len(self._observations.get(key, []))
        with self._lock:
            return sum(len(v) for v in self._observations.values())

    def sum(self, labels: dict[str, str] | None = None) -> float:
        key = _label_key(labels)
        if key:
            with self._lock:
                return sum(self._observations.get(key, []))
        with self._lock:
            return sum(sum(v) for v in self._observations.values())

    def percentile(self, p: float, labels: dict[str, str] | None = None) -> float:
        """Compute percentile. p is 0-100 (e.g. 50 for median, 99 for p99)."""
        key = _label_key(labels)
        with self._lock:
            if key:
                values = list(self._observations.get(key, []))
            else:
                values = []
                for v in self._observations.values():
                    values.extend(v)

        if not values:
            return 0

        values.sort()
        if len(values) < 2:
            return values[0]

        quantiles = statistics.quantiles(values, n=100)
        idx = max(0, min(int(p) - 1, len(quantiles) - 1))
        return quantiles[idx]

    def _snapshot(self) -> dict[str, Any]:
        with self._lock:
            all_values = []
            for v in self._observations.values():
                all_values.extend(v)

        if not all_values:
            return {
                "name": self.name,
                "type": "histogram",
                "count": 0,
                "sum": 0,
                "p50": 0,
                "p99": 0,
            }

        all_values.sort()
        if len(all_values) < 2:
            p50 = p99 = all_values[0]
        else:
            quantiles = statistics.quantiles(all_values, n=100)
            p50 = quantiles[max(0, min(49, len(quantiles) - 1))]
            p99 = quantiles[max(0, min(98, len(quantiles) - 1))]

        return {
            "name": self.name,
            "type": "histogram",
            "count": len(all_values),
            "sum": sum(all_values),
            "p50": p50,
            "p99": p99,
        }


class Timer:
    """Context manager that records elapsed time as histogram observations."""

    def __init__(self, name: str):
        self.name = name
        self.histogram = Histogram(name)

    @contextmanager
    def time(self, labels: dict[str, str] | None = None):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.histogram.observe(elapsed, labels=labels)

    def _snapshot(self) -> dict[str, Any]:
        snap = self.histogram._snapshot()
        snap["type"] = "timer"
        return snap


class MetricsRegistry:
    """Registry of all metrics. Thread-safe."""

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: dict[str, Counter | Gauge | Histogram | Timer] = {}

    def counter(self, name: str) -> Counter:
        return self._get_or_create(name, Counter)

    def gauge(self, name: str) -> Gauge:
        return self._get_or_create(name, Gauge)

    def histogram(self, name: str) -> Histogram:
        return self._get_or_create(name, Histogram)

    def timer(self, name: str) -> Timer:
        return self._get_or_create(name, Timer)

    def _get_or_create(self, name: str, metric_type: type) -> Any:
        with self._lock:
            if name in self._metrics:
                existing = self._metrics[name]
                if not isinstance(existing, metric_type):
                    raise TypeError(
                        f"Metric '{name}' already registered as {type(existing).__name__}, "
                        f"cannot re-register as {metric_type.__name__}"
                    )
                return existing
            metric = metric_type(name)
            self._metrics[name] = metric
            return metric

    def get_all(self) -> dict[str, Counter | Gauge | Histogram | Timer]:
        with self._lock:
            return dict(self._metrics)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            metrics_list = [m._snapshot() for m in self._metrics.values()]
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics_list,
        }

    def reset(self) -> None:
        with self._lock:
            self._metrics.clear()

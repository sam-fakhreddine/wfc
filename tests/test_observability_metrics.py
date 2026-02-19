"""Tests for wfc.observability.metrics — Counter, Gauge, Histogram, Timer, Registry."""

from __future__ import annotations

import json
import threading
import time

import pytest

from wfc.observability.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsRegistry,
    Timer,
)


class TestCounter:
    """Counter: monotonically increasing."""

    def test_increment_default(self):
        c = Counter("test")
        c.increment()
        assert c.get() == 1

    def test_increment_by_value(self):
        c = Counter("test")
        c.increment(5)
        c.increment(3)
        assert c.get() == 8

    def test_no_decrement_method(self):
        c = Counter("test")
        assert not hasattr(c, "decrement")

    def test_negative_increment_raises(self):
        c = Counter("test")
        with pytest.raises(ValueError):
            c.increment(-1)

    def test_labels_isolation(self):
        c = Counter("labeled")
        c.increment(labels={"reviewer": "security"})
        c.increment(labels={"reviewer": "security"})
        c.increment(labels={"reviewer": "correctness"})
        assert c.get(labels={"reviewer": "security"}) == 2
        assert c.get(labels={"reviewer": "correctness"}) == 1

    def test_total_across_labels(self):
        c = Counter("labeled")
        c.increment(3, labels={"a": "1"})
        c.increment(2, labels={"a": "2"})
        assert c.get() == 5

    def test_thread_safety(self):
        c = Counter("concurrent")
        threads = []
        for _ in range(100):
            t = threading.Thread(target=lambda: [c.increment() for _ in range(1000)])
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert c.get() == 100_000


class TestGauge:
    """Gauge: arbitrary value."""

    def test_set(self):
        g = Gauge("test")
        g.set(42)
        assert g.get() == 42

    def test_increment(self):
        g = Gauge("test")
        g.set(10)
        g.increment()
        assert g.get() == 11

    def test_increment_by(self):
        g = Gauge("test")
        g.set(10)
        g.increment(5)
        assert g.get() == 15

    def test_decrement(self):
        g = Gauge("test")
        g.set(10)
        g.decrement()
        assert g.get() == 9

    def test_decrement_by(self):
        g = Gauge("test")
        g.set(10)
        g.decrement(3)
        assert g.get() == 7

    def test_negative_value(self):
        g = Gauge("test")
        g.set(-10)
        assert g.get() == -10

    def test_labels(self):
        g = Gauge("labeled")
        g.set(1, labels={"a": "1"})
        g.set(2, labels={"a": "2"})
        assert g.get(labels={"a": "1"}) == 1
        assert g.get(labels={"a": "2"}) == 2

    def test_default_value_zero(self):
        g = Gauge("test")
        assert g.get() == 0


class TestHistogram:
    """Histogram: distribution with percentiles."""

    def test_observe(self):
        h = Histogram("test")
        for v in [1, 2, 3, 4, 5]:
            h.observe(v)
        assert h.count() == 5
        assert h.sum() == 15

    def test_percentile_median(self):
        h = Histogram("test")
        for v in range(1, 101):
            h.observe(v)
        p50 = h.percentile(50)
        assert 45 <= p50 <= 55

    def test_percentile_p99(self):
        h = Histogram("test")
        for v in range(1, 101):
            h.observe(v)
        p99 = h.percentile(99)
        assert p99 >= 95

    def test_empty_percentile(self):
        h = Histogram("test")
        assert h.percentile(50) == 0

    def test_labels(self):
        h = Histogram("labeled")
        h.observe(1.0, labels={"op": "read"})
        h.observe(2.0, labels={"op": "write"})
        assert h.count(labels={"op": "read"}) == 1
        assert h.count(labels={"op": "write"}) == 1


class TestTimer:
    """Timer: context manager recording duration."""

    def test_context_manager(self):
        t = Timer("test")
        with t.time():
            time.sleep(0.01)
        assert t.histogram.count() == 1
        assert t.histogram.percentile(50) >= 0.01

    def test_labels(self):
        t = Timer("test")
        with t.time(labels={"phase": "dedup"}):
            time.sleep(0.01)
        assert t.histogram.count(labels={"phase": "dedup"}) == 1

    def test_exception_still_records(self):
        t = Timer("test")
        with pytest.raises(ValueError):
            with t.time():
                raise ValueError("boom")
        assert t.histogram.count() == 1


class TestMetricsRegistry:
    """MetricsRegistry: singleton, snapshot, reset."""

    def test_counter_creation(self):
        r = MetricsRegistry()
        c = r.counter("test_counter")
        assert isinstance(c, Counter)

    def test_same_name_returns_same_instance(self):
        r = MetricsRegistry()
        c1 = r.counter("same")
        c2 = r.counter("same")
        assert c1 is c2

    def test_gauge_creation(self):
        r = MetricsRegistry()
        g = r.gauge("test_gauge")
        assert isinstance(g, Gauge)

    def test_histogram_creation(self):
        r = MetricsRegistry()
        h = r.histogram("test_hist")
        assert isinstance(h, Histogram)

    def test_timer_creation(self):
        r = MetricsRegistry()
        t = r.timer("test_timer")
        assert isinstance(t, Timer)

    def test_snapshot_json_serializable(self):
        r = MetricsRegistry()
        c = r.counter("snap_counter")
        c.increment(5)
        g = r.gauge("snap_gauge")
        g.set(42)
        snapshot = r.snapshot()
        json_str = json.dumps(snapshot)
        assert "snap_counter" in json_str
        assert "snap_gauge" in json_str

    def test_snapshot_contains_all_metrics(self):
        r = MetricsRegistry()
        r.counter("c1").increment()
        r.gauge("g1").set(1)
        r.histogram("h1").observe(1.0)
        snapshot = r.snapshot()
        names = {m["name"] for m in snapshot["metrics"]}
        assert names == {"c1", "g1", "h1"}

    def test_reset_clears_all(self):
        r = MetricsRegistry()
        r.counter("c").increment(10)
        r.gauge("g").set(42)
        r.reset()
        snapshot = r.snapshot()
        assert len(snapshot["metrics"]) == 0

    def test_get_all(self):
        r = MetricsRegistry()
        r.counter("a")
        r.gauge("b")
        all_metrics = r.get_all()
        assert len(all_metrics) == 2

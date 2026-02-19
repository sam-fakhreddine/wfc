"""Tests for wfc.observability.instrument — safe emit/metric helpers + integration."""

from __future__ import annotations

import pytest

import wfc.observability as obs
from wfc.observability.instrument import emit_event, gauge_set, incr, observe, timed
from wfc.observability.providers.memory_provider import InMemoryProvider


@pytest.fixture(autouse=True)
def _setup_obs(monkeypatch):
    """Init observability with InMemoryProvider for each test."""
    obs.reset()
    monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
    obs.init()
    yield
    obs.reset()


def _get_memory_provider() -> InMemoryProvider:
    pr = obs.get_provider_registry()
    return [p for p in pr.providers if isinstance(p, InMemoryProvider)][0]


class TestEmitEvent:
    """Test safe event emission."""

    def test_emit_event_reaches_provider(self):
        emit_event("test.happened", source="test", payload={"k": "v"})
        mem = _get_memory_provider()
        assert len(mem.events) == 1
        assert mem.events[0].event_type == "test.happened"

    def test_emit_event_with_level(self):
        emit_event("test.error", source="test", level="error")
        mem = _get_memory_provider()
        assert mem.events[0].level == "error"

    def test_emit_event_does_not_raise_when_uninitialized(self):
        obs.reset()
        emit_event("test.no_init", source="test")


class TestIncr:
    """Test safe counter increment."""

    def test_incr_records_counter(self):
        incr("test.count")
        incr("test.count")
        registry = obs.get_registry()
        assert registry.counter("test.count").get() == 2

    def test_incr_with_labels(self):
        incr("test.labeled", labels={"reviewer": "security"})
        registry = obs.get_registry()
        assert registry.counter("test.labeled").get(labels={"reviewer": "security"}) == 1

    def test_incr_does_not_raise_when_uninitialized(self):
        obs.reset()
        incr("test.no_init")


class TestGaugeSet:
    """Test safe gauge set."""

    def test_gauge_set_records(self):
        gauge_set("test.gauge", 42)
        registry = obs.get_registry()
        assert registry.gauge("test.gauge").get() == 42

    def test_gauge_set_does_not_raise_when_uninitialized(self):
        obs.reset()
        gauge_set("test.no_init", 1)


class TestTimed:
    """Test safe timing context manager."""

    def test_timed_records_histogram(self):
        with timed("test.duration"):
            pass
        registry = obs.get_registry()
        assert registry.histogram("test.duration").count() == 1

    def test_timed_records_on_exception(self):
        with pytest.raises(ValueError):
            with timed("test.error_duration"):
                raise ValueError("boom")
        registry = obs.get_registry()
        assert registry.histogram("test.error_duration").count() == 1

    def test_timed_does_not_raise_when_uninitialized(self):
        obs.reset()
        with timed("test.no_init"):
            pass


class TestObserve:
    """Test safe histogram observation."""

    def test_observe_records(self):
        observe("test.hist", 3.14)
        registry = obs.get_registry()
        assert registry.histogram("test.hist").count() == 1

    def test_observe_does_not_raise_when_uninitialized(self):
        obs.reset()
        observe("test.no_init", 1.0)

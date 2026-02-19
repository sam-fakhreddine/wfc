"""Tests for wfc.observability init/shutdown flow (TASK-005)."""

from __future__ import annotations

import pytest

import wfc.observability as obs
from wfc.observability.events import ObservabilityEvent
from wfc.observability.metrics import MetricsRegistry
from wfc.observability.providers.memory_provider import InMemoryProvider


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset observability state between tests."""
    obs.reset()
    yield
    obs.reset()


class TestInit:
    """Test initialization flow."""

    def test_init_sets_initialized(self):
        obs.init()
        assert obs.is_initialized()

    def test_init_idempotent(self):
        obs.init()
        obs.init()
        assert obs.is_initialized()

    def test_get_registry_returns_metrics_registry(self):
        registry = obs.get_registry()
        assert isinstance(registry, MetricsRegistry)

    def test_get_bus_auto_inits(self):
        assert not obs.is_initialized()
        bus = obs.get_bus()
        assert obs.is_initialized()
        assert bus is not None

    def test_get_provider_registry_auto_inits(self):
        pr = obs.get_provider_registry()
        assert pr is not None
        assert obs.is_initialized()


class TestShutdown:
    """Test shutdown flow."""

    def test_shutdown_resets_initialized(self):
        obs.init()
        assert obs.is_initialized()
        obs.shutdown()
        assert not obs.is_initialized()

    def test_shutdown_idempotent(self):
        obs.init()
        obs.shutdown()
        obs.shutdown()

    def test_shutdown_without_init_is_safe(self):
        obs.shutdown()


class TestEventToProviderBridge:
    """Test that events flow from bus to providers."""

    def test_events_reach_provider(self, monkeypatch):
        monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
        obs.init()

        pr = obs.get_provider_registry()
        mem_providers = [p for p in pr.providers if isinstance(p, InMemoryProvider)]
        assert len(mem_providers) == 1
        mem = mem_providers[0]

        bus = obs.get_bus()
        bus.emit(
            ObservabilityEvent(
                event_type="test.event",
                source="test",
                session_id="s",
                payload={"k": "v"},
            )
        )

        assert len(mem.events) == 1
        assert mem.events[0].event_type == "test.event"

    def test_metrics_snapshot_reaches_provider(self, monkeypatch):
        monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
        obs.init()

        registry = obs.get_registry()
        registry.counter("test.counter").increment(5)

        pr = obs.get_provider_registry()
        mem_providers = [p for p in pr.providers if isinstance(p, InMemoryProvider)]
        mem = mem_providers[0]

        snapshot = registry.snapshot()
        pr.push_snapshot(snapshot)

        assert len(mem.snapshots) == 1
        assert any(m["name"] == "test.counter" for m in mem.snapshots[0]["metrics"])


class TestReset:
    """Test reset for test isolation."""

    def test_reset_clears_everything(self):
        obs.init()
        registry = obs.get_registry()
        registry.counter("c").increment()
        obs.reset()
        assert not obs.is_initialized()

    def test_re_init_after_reset(self):
        obs.init()
        obs.reset()
        obs.init()
        assert obs.is_initialized()


class TestLazyImport:
    """Test that importing alone does nothing."""

    def test_import_does_not_init(self):
        assert not obs.is_initialized()

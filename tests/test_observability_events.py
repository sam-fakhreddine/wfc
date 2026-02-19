"""Tests for wfc.observability.events — ObservabilityEvent and EventBus."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from wfc.observability.events import EventBus, ObservabilityEvent


class TestObservabilityEvent:
    """Test event dataclass."""

    def test_create_event(self):
        event = ObservabilityEvent(
            event_type="review.started",
            source="orchestrator",
            session_id="test-session",
            payload={"task_id": "TASK-001"},
        )
        assert event.event_type == "review.started"
        assert event.source == "orchestrator"
        assert event.session_id == "test-session"
        assert event.payload == {"task_id": "TASK-001"}
        assert event.level == "info"

    def test_timestamp_auto_generated(self):
        event = ObservabilityEvent(
            event_type="test",
            source="test",
            session_id="s",
            payload={},
        )
        assert event.timestamp
        assert "T" in event.timestamp

    def test_to_dict(self):
        event = ObservabilityEvent(
            event_type="test.event",
            source="test",
            session_id="s1",
            payload={"key": "value"},
            level="warning",
        )
        d = event.to_dict()
        assert d["event_type"] == "test.event"
        assert d["source"] == "test"
        assert d["payload"] == {"key": "value"}
        assert d["level"] == "warning"


class TestEventBus:
    """Test simplified direct-dispatch EventBus."""

    def test_emit_to_no_providers(self):
        """Emit with no providers registered — no error."""
        bus = EventBus()
        event = ObservabilityEvent(
            event_type="test", source="test", session_id="s", payload={}
        )
        bus.emit(event)

    def test_emit_dispatches_to_provider(self):
        bus = EventBus()
        provider = MagicMock()
        bus.register_provider(provider)

        event = ObservabilityEvent(
            event_type="test.event", source="test", session_id="s", payload={}
        )
        bus.emit(event)

        provider.on_event.assert_called_once_with(event)

    def test_emit_dispatches_to_multiple_providers(self):
        bus = EventBus()
        p1 = MagicMock()
        p2 = MagicMock()
        bus.register_provider(p1)
        bus.register_provider(p2)

        event = ObservabilityEvent(
            event_type="test", source="test", session_id="s", payload={}
        )
        bus.emit(event)

        p1.on_event.assert_called_once_with(event)
        p2.on_event.assert_called_once_with(event)

    def test_provider_error_isolated(self):
        """Failing provider doesn't block others."""
        bus = EventBus()
        bad_provider = MagicMock()
        bad_provider.on_event.side_effect = RuntimeError("boom")
        good_provider = MagicMock()
        bus.register_provider(bad_provider)
        bus.register_provider(good_provider)

        event = ObservabilityEvent(
            event_type="test", source="test", session_id="s", payload={}
        )
        bus.emit(event)

        good_provider.on_event.assert_called_once_with(event)

    def test_unregister_provider(self):
        bus = EventBus()
        provider = MagicMock()
        bus.register_provider(provider)
        bus.unregister_provider(provider)

        event = ObservabilityEvent(
            event_type="test", source="test", session_id="s", payload={}
        )
        bus.emit(event)

        provider.on_event.assert_not_called()

    def test_thread_safe_emit(self):
        """Concurrent emits don't crash."""
        bus = EventBus()
        received = []
        provider = MagicMock()
        provider.on_event.side_effect = lambda e: received.append(e)
        bus.register_provider(provider)

        def emit_many():
            for i in range(100):
                bus.emit(
                    ObservabilityEvent(
                        event_type="test", source="test", session_id="s", payload={"i": i}
                    )
                )

        threads = [threading.Thread(target=emit_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(received) == 1000

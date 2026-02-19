"""Tests for wfc.observability.providers — ABC, Registry, and built-in providers."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from wfc.observability.events import ObservabilityEvent
from wfc.observability.providers import (
    ObservabilityProvider,
    ProviderRegistry,
)
from wfc.observability.providers.console_provider import ConsoleProvider
from wfc.observability.providers.file_provider import FileProvider
from wfc.observability.providers.memory_provider import InMemoryProvider
from wfc.observability.providers.null_provider import NullProvider


def _make_event(event_type: str = "test.event", level: str = "info") -> ObservabilityEvent:
    return ObservabilityEvent(
        event_type=event_type,
        source="test",
        session_id="test-session",
        payload={"key": "value"},
        level=level,
    )


class TestObservabilityProviderABC:
    """Test abstract base class."""

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            ObservabilityProvider()  # type: ignore[abstract]

    def test_requires_four_methods(self):
        class Incomplete(ObservabilityProvider):
            def on_event(self, event):
                pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]

    def test_api_version_exists(self):
        assert hasattr(ObservabilityProvider, "PROVIDER_API_VERSION")
        assert ObservabilityProvider.PROVIDER_API_VERSION == 1


class TestNullProvider:
    """NullProvider: no-op."""

    def test_on_event_noop(self):
        p = NullProvider()
        p.on_event(_make_event())

    def test_on_metric_snapshot_noop(self):
        p = NullProvider()
        p.on_metric_snapshot({"metrics": []})

    def test_flush_noop(self):
        p = NullProvider()
        p.flush()

    def test_close_noop(self):
        p = NullProvider()
        p.close()


class TestInMemoryProvider:
    """InMemoryProvider: list storage with query."""

    def test_captures_events(self):
        p = InMemoryProvider()
        p.on_event(_make_event("a"))
        p.on_event(_make_event("b"))
        assert len(p.events) == 2

    def test_find_by_type(self):
        p = InMemoryProvider()
        p.on_event(_make_event("hook.decision"))
        p.on_event(_make_event("review.started"))
        p.on_event(_make_event("hook.error"))
        results = p.find(event_type="hook.decision")
        assert len(results) == 1
        assert results[0].event_type == "hook.decision"

    def test_find_by_type_prefix(self):
        p = InMemoryProvider()
        p.on_event(_make_event("hook.decision"))
        p.on_event(_make_event("hook.error"))
        p.on_event(_make_event("review.started"))
        results = p.find(event_type_prefix="hook.")
        assert len(results) == 2

    def test_clear(self):
        p = InMemoryProvider()
        p.on_event(_make_event())
        p.on_event(_make_event())
        assert len(p.events) == 2
        p.clear()
        assert len(p.events) == 0

    def test_captures_snapshots(self):
        p = InMemoryProvider()
        p.on_metric_snapshot({"metrics": [{"name": "test", "value": 1}]})
        assert len(p.snapshots) == 1


class TestFileProvider:
    """FileProvider: JSON-lines output."""

    def test_writes_jsonlines(self, tmp_path):
        p = FileProvider(output_dir=str(tmp_path), session_id="test-123")
        p.on_event(_make_event("event.one"))
        p.on_event(_make_event("event.two"))
        p.on_event(_make_event("event.three"))
        p.flush()

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1

        lines = files[0].read_text().strip().split("\n")
        assert len(lines) == 3

        for line in lines:
            data = json.loads(line)
            assert "event_type" in data
            assert "timestamp" in data

    def test_session_in_filename(self, tmp_path):
        p = FileProvider(output_dir=str(tmp_path), session_id="abc-123")
        p.on_event(_make_event())
        p.flush()

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        assert "abc-123" in files[0].name

    def test_creates_output_dir(self, tmp_path):
        output_dir = tmp_path / "sub" / "dir"
        p = FileProvider(output_dir=str(output_dir), session_id="test")
        p.on_event(_make_event())
        p.flush()
        assert output_dir.exists()

    def test_writes_metric_snapshots(self, tmp_path):
        p = FileProvider(output_dir=str(tmp_path), session_id="test")
        p.on_metric_snapshot({"timestamp": "2026-01-01", "metrics": []})
        p.flush()

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        data = json.loads(files[0].read_text().strip())
        assert data["_type"] == "metric_snapshot"

    def test_close_flushes(self, tmp_path):
        p = FileProvider(output_dir=str(tmp_path), session_id="test")
        p.on_event(_make_event())
        p.close()

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1

    @pytest.mark.parametrize(
        "malicious_id",
        [
            "../etc/passwd",
            "..\\windows\\system32",
            ".../bypass",
            "../../secret",
            "valid/../../escape",
        ],
    )
    def test_session_id_path_traversal_safe(self, tmp_path, malicious_id):
        p = FileProvider(output_dir=str(tmp_path), session_id=malicious_id)
        p.on_event(_make_event())
        p.flush()

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        assert files[0].resolve().parent == tmp_path.resolve()
        assert "/" not in p._session_id
        assert "\\" not in p._session_id


class TestConsoleProvider:
    """ConsoleProvider: stderr output."""

    def test_on_event_writes_to_stderr(self, capsys):
        p = ConsoleProvider(verbosity=2)
        p.on_event(_make_event("test.event"))
        captured = capsys.readouterr()
        assert "test.event" in captured.err

    def test_verbosity_0_errors_only(self, capsys):
        p = ConsoleProvider(verbosity=0)
        p.on_event(_make_event("test.info", level="info"))
        p.on_event(_make_event("test.error", level="error"))
        captured = capsys.readouterr()
        assert "test.info" not in captured.err
        assert "test.error" in captured.err

    def test_verbosity_1_decisions(self, capsys):
        p = ConsoleProvider(verbosity=1)
        p.on_event(_make_event("test.info", level="info"))
        p.on_event(_make_event("test.warning", level="warning"))
        captured = capsys.readouterr()
        assert "test.info" not in captured.err
        assert "test.warning" in captured.err

    def test_respects_no_color(self, capsys, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        p = ConsoleProvider(verbosity=2)
        p.on_event(_make_event("test.event"))
        captured = capsys.readouterr()
        assert "\033[" not in captured.err
        assert "test.event" in captured.err


class TestProviderRegistry:
    """ProviderRegistry: manage providers."""

    def test_register_and_unregister(self):
        reg = ProviderRegistry()
        p = NullProvider()
        reg.register(p)
        assert p in reg.providers
        reg.unregister(p)
        assert p not in reg.providers

    def test_push_snapshot(self):
        reg = ProviderRegistry()
        p = InMemoryProvider()
        reg.register(p)
        reg.push_snapshot({"metrics": []})
        assert len(p.snapshots) == 1

    def test_flush_all(self):
        reg = ProviderRegistry()
        p = MagicMock()
        reg.register(p)
        reg.flush_all()
        p.flush.assert_called_once()

    def test_close_all(self):
        reg = ProviderRegistry()
        p = MagicMock()
        reg.register(p)
        reg.close_all()
        p.close.assert_called_once()

    def test_error_isolation_on_flush(self):
        reg = ProviderRegistry()
        bad = MagicMock()
        bad.flush.side_effect = RuntimeError("disk full")
        good = MagicMock()
        reg.register(bad)
        reg.register(good)
        reg.flush_all()
        good.flush.assert_called_once()

    def test_error_isolation_on_push_snapshot(self):
        reg = ProviderRegistry()
        bad = MagicMock()
        bad.on_metric_snapshot.side_effect = RuntimeError("boom")
        good = InMemoryProvider()
        reg.register(bad)
        reg.register(good)
        reg.push_snapshot({"metrics": []})
        assert len(good.snapshots) == 1

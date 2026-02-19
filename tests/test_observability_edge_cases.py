"""Tests for TASK-011: Edge cases and backward compatibility."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import wfc.observability as obs
from wfc.observability.events import ObservabilityEvent
from wfc.observability.providers import ProviderRegistry
from wfc.observability.providers.file_provider import FileProvider
from wfc.observability.providers.memory_provider import InMemoryProvider


@pytest.fixture(autouse=True)
def _clean():
    obs.reset()
    yield
    obs.reset()


class TestEdgeCases:
    """Edge cases that must not crash."""

    def test_empty_review_instrumentation(self, monkeypatch):
        """Empty review (0 files) doesn't crash instrumentation."""
        monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
        obs.init()

        from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator, ReviewRequest

        engine = MagicMock()
        engine.prepare_review_tasks.return_value = []
        orch = ReviewOrchestrator(reviewer_engine=engine)

        request = ReviewRequest(task_id="EMPTY", files=[])
        result = orch.prepare_review(request)
        assert result == []

        pr = obs.get_provider_registry()
        mem = [p for p in pr.providers if isinstance(p, InMemoryProvider)][0]
        started = [e for e in mem.events if e.event_type == "review.started"]
        assert len(started) == 1
        assert started[0].payload["file_count"] == 0

    def test_provider_crash_during_flush(self):
        """Provider crash during flush doesn't propagate."""
        reg = ProviderRegistry()
        bad = MagicMock()
        bad.flush.side_effect = OSError("disk full")
        good = MagicMock()
        reg.register(bad)
        reg.register(good)
        reg.flush_all()
        good.flush.assert_called_once()

    def test_eventbus_with_no_providers(self, monkeypatch):
        """EventBus with no providers doesn't error."""
        from wfc.observability.events import EventBus

        bus = EventBus()
        bus.emit(ObservabilityEvent(event_type="test", source="test", session_id="s", payload={}))

    def test_missing_config_falls_back_silently(self, tmp_path, monkeypatch):
        """Missing config file falls back to defaults without errors."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("WFC_OBSERVABILITY_PROVIDERS", raising=False)
        obs.init()
        assert obs.is_initialized()

    def test_malformed_toml_falls_back(self, tmp_path, monkeypatch):
        """Malformed TOML config falls back to defaults."""
        wfc_dir = tmp_path / ".wfc"
        wfc_dir.mkdir()
        (wfc_dir / "observability.toml").write_text("broken [[[toml content")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("WFC_OBSERVABILITY_PROVIDERS", raising=False)
        obs.init()
        assert obs.is_initialized()

    def test_clean_import_no_side_effects(self):
        """Importing wfc.observability with no config has zero side effects."""
        obs.reset()
        import wfc.observability as _obs  # noqa: F811

        assert not _obs.is_initialized()

    def test_concurrent_file_providers(self, tmp_path):
        """Two FileProviders with different sessions create separate files."""
        p1 = FileProvider(output_dir=str(tmp_path), session_id="session-A")
        p2 = FileProvider(output_dir=str(tmp_path), session_id="session-B")

        event = ObservabilityEvent(event_type="test", source="test", session_id="s", payload={})
        p1.on_event(event)
        p2.on_event(event)
        p1.flush()
        p2.flush()

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 2
        names = {f.name for f in files}
        assert any("session-A" in n for n in names)
        assert any("session-B" in n for n in names)

    def test_metrics_with_empty_labels(self, monkeypatch):
        """Metrics with empty labels dict work normally."""
        monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
        obs.init()
        registry = obs.get_registry()
        c = registry.counter("empty_labels")
        c.increment(labels={})
        assert c.get() == 1


class TestBackwardCompatibility:
    """Verify no breaking changes to public APIs."""

    def test_review_orchestrator_init_signature(self):
        from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator

        import inspect

        sig = inspect.signature(ReviewOrchestrator.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "reviewer_engine" in params
        assert "retriever" in params

    def test_review_orchestrator_prepare_review_signature(self):
        from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator

        import inspect

        sig = inspect.signature(ReviewOrchestrator.prepare_review)
        params = list(sig.parameters.keys())
        assert params == ["self", "request"]

    def test_review_orchestrator_finalize_review_signature(self):
        from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator

        import inspect

        sig = inspect.signature(ReviewOrchestrator.finalize_review)
        params = list(sig.parameters.keys())
        assert params == ["self", "request", "task_responses", "output_dir", "skip_validation"]

    def test_security_hook_check_signature(self):
        from wfc.scripts.hooks.security_hook import check

        import inspect

        sig = inspect.signature(check)
        params = list(sig.parameters.keys())
        assert params == ["input_data", "state"]

    def test_rule_engine_evaluate_signature(self):
        from wfc.scripts.hooks.rule_engine import evaluate

        import inspect

        sig = inspect.signature(evaluate)
        params = list(sig.parameters.keys())
        assert params == ["input_data", "rules_dir"]

    def test_drift_detector_analyze_signature(self):
        from wfc.scripts.knowledge.drift_detector import DriftDetector

        import inspect

        sig = inspect.signature(DriftDetector.analyze)
        params = list(sig.parameters.keys())
        assert params == ["self"]

"""Tests for TASK-006: ReviewOrchestrator instrumentation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import wfc.observability as obs
from wfc.observability.providers.memory_provider import InMemoryProvider
from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator, ReviewRequest


@pytest.fixture(autouse=True)
def _setup_obs(monkeypatch):
    obs.reset()
    monkeypatch.setenv("WFC_OBSERVABILITY_PROVIDERS", "memory")
    obs.init()
    yield
    obs.reset()


def _get_memory_provider() -> InMemoryProvider:
    pr = obs.get_provider_registry()
    return [p for p in pr.providers if isinstance(p, InMemoryProvider)][0]


class TestReviewOrchestratorInstrumentation:
    """Test that orchestrator emits events and records metrics."""

    def test_prepare_review_emits_started(self):
        engine = MagicMock()
        engine.prepare_review_tasks.return_value = []
        orch = ReviewOrchestrator(reviewer_engine=engine)

        request = ReviewRequest(task_id="T-001", files=["a.py", "b.py"])
        orch.prepare_review(request)

        mem = _get_memory_provider()
        started = [e for e in mem.events if e.event_type == "review.started"]
        assert len(started) == 1
        assert started[0].payload["task_id"] == "T-001"
        assert started[0].payload["file_count"] == 2

    def test_finalize_review_emits_scored_and_completed(self, tmp_path):
        engine = MagicMock()
        engine.parse_results.return_value = []
        fingerprinter = MagicMock()
        fingerprinter.deduplicate.return_value = []
        scorer = MagicMock()
        scorer.calculate.return_value = MagicMock(
            cs=3.5, tier="informational", passed=True,
            minority_protection_applied=False, findings=[], summary="ok",
            n=5, R_bar=0, R_max=0, k_total=0,
        )

        orch = ReviewOrchestrator(reviewer_engine=engine)
        orch.fingerprinter = fingerprinter
        orch.scorer = scorer

        request = ReviewRequest(task_id="T-002", files=["x.py"])
        orch._generate_report = MagicMock()

        orch.finalize_review(request, [], tmp_path)

        mem = _get_memory_provider()
        scored = [e for e in mem.events if e.event_type == "review.scored"]
        completed = [e for e in mem.events if e.event_type == "review.completed"]

        assert len(scored) == 1
        assert scored[0].payload["cs"] == 3.5
        assert scored[0].payload["tier"] == "informational"

        assert len(completed) == 1
        assert completed[0].payload["task_id"] == "T-002"
        assert "duration_seconds" in completed[0].payload

    def test_instrumentation_failure_does_not_block_review(self, tmp_path):
        """Even if observability breaks, review must succeed."""
        engine = MagicMock()
        engine.prepare_review_tasks.return_value = []

        orch = ReviewOrchestrator(reviewer_engine=engine)

        obs.reset()

        request = ReviewRequest(task_id="T-003", files=["a.py"])
        result = orch.prepare_review(request)
        assert result == []

    def test_review_counter_incremented(self, tmp_path):
        engine = MagicMock()
        engine.parse_results.return_value = []
        fingerprinter = MagicMock()
        fingerprinter.deduplicate.return_value = []
        scorer = MagicMock()
        scorer.calculate.return_value = MagicMock(
            cs=2.0, tier="informational", passed=True,
            minority_protection_applied=False, findings=[], summary="ok",
            n=5, R_bar=0, R_max=0, k_total=0,
        )

        orch = ReviewOrchestrator(reviewer_engine=engine)
        orch.fingerprinter = fingerprinter
        orch.scorer = scorer
        orch._generate_report = MagicMock()

        request = ReviewRequest(task_id="T-004", files=["a.py"])
        orch.finalize_review(request, [], tmp_path)

        registry = obs.get_registry()
        assert registry.counter("review.completed").get() == 1

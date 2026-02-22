"""Tests for ReviewOrchestrator."""

from wfc.scripts.orchestrators.review.orchestrator import ReviewOrchestrator


def test_orchestrator_default_use_diff_manifest():
    """Test that use_diff_manifest defaults to False for backward compatibility."""
    orchestrator = ReviewOrchestrator()
    assert orchestrator.use_diff_manifest is False


def test_orchestrator_use_diff_manifest_true():
    """Test that use_diff_manifest can be set to True."""
    orchestrator = ReviewOrchestrator(use_diff_manifest=True)
    assert orchestrator.use_diff_manifest is True


def test_orchestrator_use_diff_manifest_false():
    """Test that use_diff_manifest can be explicitly set to False."""
    orchestrator = ReviewOrchestrator(use_diff_manifest=False)
    assert orchestrator.use_diff_manifest is False


def test_orchestrator_stores_use_diff_manifest():
    """Test that use_diff_manifest is stored as instance variable."""
    orchestrator = ReviewOrchestrator(use_diff_manifest=True)
    assert hasattr(orchestrator, "use_diff_manifest")
    assert orchestrator.use_diff_manifest is True


def test_token_metrics_logged():
    """Test that token metrics are logged when using diff manifests."""
    from wfc.scripts.orchestrators.review.reviewer_engine import ReviewerEngine

    engine = ReviewerEngine()
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -10,1 +10,1 @@
-old
+new
"""

    tasks = engine.prepare_review_tasks(
        files=["test.py"], diff_content=diff, use_diff_manifest=True
    )

    tasks_with_metrics = [t for t in tasks if "token_metrics" in t]
    assert len(tasks_with_metrics) > 0

    for task in tasks_with_metrics:
        metrics = task["token_metrics"]
        assert "full_diff_tokens" in metrics
        assert "manifest_tokens" in metrics
        assert "reduction_pct" in metrics
        assert isinstance(metrics["full_diff_tokens"], int)
        assert isinstance(metrics["manifest_tokens"], int)
        assert isinstance(metrics["reduction_pct"], float)

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

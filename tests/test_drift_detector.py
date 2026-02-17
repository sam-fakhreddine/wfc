"""Tests for knowledge drift detection (TASK-014).

TDD — these tests are written FIRST, before the implementation.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from wfc.scripts.knowledge.drift_detector import (
    DriftDetector,
    DriftReport,
    DriftSignal,
)


def _write_knowledge(path: Path, content: str) -> Path:
    """Helper: write a KNOWLEDGE.md file inside a reviewer dir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def _make_reviewer_dir(tmp_path: Path, reviewer_id: str, content: str) -> Path:
    """Create a reviewer directory with a KNOWLEDGE.md."""
    reviewer_dir = tmp_path / "reviewers" / reviewer_id
    reviewer_dir.mkdir(parents=True, exist_ok=True)
    km = reviewer_dir / "KNOWLEDGE.md"
    km.write_text(content)
    return reviewer_dir




def test_drift_signal_fields():
    """DriftSignal has all required fields."""
    signal = DriftSignal(
        reviewer_id="security",
        signal_type="stale",
        severity="medium",
        description="Entry is 120 days old",
        file_path="/some/path/KNOWLEDGE.md",
        line_range=(5, 5),
    )
    assert signal.reviewer_id == "security"
    assert signal.signal_type == "stale"
    assert signal.severity == "medium"
    assert signal.description == "Entry is 120 days old"
    assert signal.file_path == "/some/path/KNOWLEDGE.md"
    assert signal.line_range == (5, 5)


def test_drift_signal_line_range_optional():
    """DriftSignal.line_range defaults to None."""
    signal = DriftSignal(
        reviewer_id="security",
        signal_type="stale",
        severity="low",
        description="test",
        file_path="/tmp/KNOWLEDGE.md",
    )
    assert signal.line_range is None




def test_no_knowledge_files_healthy(tmp_path: Path):
    """Empty dir → healthy report."""
    reviewers_dir = tmp_path / "reviewers"
    reviewers_dir.mkdir()
    detector = DriftDetector(reviewers_dir=reviewers_dir)
    report = detector.analyze()
    assert isinstance(report, DriftReport)
    assert report.signals == []
    assert report.recommendation == "healthy"
    assert report.total_entries == 0
    assert report.healthy_count == 0




def test_fresh_entries_not_stale(tmp_path: Path):
    """Recent entries (within 90 days) produce no stale signals."""
    today = date.today().isoformat()
    content = f"""# KNOWLEDGE.md -- Security Reviewer

## Patterns Found

- [{today}] SQL injection found in `app/db.py:42` (Source: review-1)
- [{today}] XSS in template (Source: review-2)
"""
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    signals = detector.check_staleness(
        tmp_path / "reviewers" / "security" / "KNOWLEDGE.md", "security"
    )
    assert signals == []


def test_old_entries_stale(tmp_path: Path):
    """Entries older than 90 days produce stale signals."""
    old_date = (date.today() - timedelta(days=120)).isoformat()
    content = f"""# KNOWLEDGE.md -- Security Reviewer

## Patterns Found

- [{old_date}] Old pattern in `app/old.py:1` (Source: review-1)
"""
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    signals = detector.check_staleness(
        tmp_path / "reviewers" / "security" / "KNOWLEDGE.md", "security"
    )
    assert len(signals) == 1
    assert signals[0].signal_type == "stale"
    assert signals[0].reviewer_id == "security"
    assert signals[0].severity == "medium"




def test_many_entries_bloated(tmp_path: Path):
    """>50 entries → bloated signal."""
    today = date.today().isoformat()
    lines = [f"- [{today}] Entry number {i} (Source: test)" for i in range(55)]
    content = "## Patterns Found\n\n" + "\n".join(lines) + "\n"
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    signals = detector.check_bloat(
        tmp_path / "reviewers" / "security" / "KNOWLEDGE.md", "security"
    )
    assert len(signals) == 1
    assert signals[0].signal_type == "bloated"
    assert signals[0].severity == "high"


def test_few_entries_not_bloated(tmp_path: Path):
    """<50 entries → no bloat signal."""
    today = date.today().isoformat()
    lines = [f"- [{today}] Entry number {i} (Source: test)" for i in range(10)]
    content = "## Patterns Found\n\n" + "\n".join(lines) + "\n"
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    signals = detector.check_bloat(
        tmp_path / "reviewers" / "security" / "KNOWLEDGE.md", "security"
    )
    assert signals == []




def test_contradiction_detected(tmp_path: Path):
    """Same path in Patterns Found and False Positives → contradictory signal."""
    today = date.today().isoformat()
    content = f"""## Patterns Found

- [{today}] SQL injection in `app/db.py:42` -- use parameterized queries (Source: r1)

## False Positives to Avoid

- [{today}] `app/db.py:42` flagged but it's actually safe (Source: r2)
"""
    _make_reviewer_dir(tmp_path, "correctness", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    signals = detector.check_contradictions(
        tmp_path / "reviewers" / "correctness" / "KNOWLEDGE.md", "correctness"
    )
    assert len(signals) >= 1
    assert signals[0].signal_type == "contradictory"
    assert signals[0].severity == "high"
    assert "app/db.py" in signals[0].description


def test_no_contradiction_different_paths(tmp_path: Path):
    """Different paths in Patterns and FalsePositives → no contradiction."""
    today = date.today().isoformat()
    content = f"""## Patterns Found

- [{today}] Issue in `app/db.py:42` (Source: r1)

## False Positives to Avoid

- [{today}] `app/auth.py:15` is actually safe (Source: r2)
"""
    _make_reviewer_dir(tmp_path, "correctness", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    signals = detector.check_contradictions(
        tmp_path / "reviewers" / "correctness" / "KNOWLEDGE.md", "correctness"
    )
    assert signals == []




def test_orphaned_file_detected(tmp_path: Path):
    """Path in entry that doesn't exist on disk → orphaned signal."""
    today = date.today().isoformat()
    content = f"""## Patterns Found

- [{today}] Issue in `nonexistent/file.py:10` (Source: r1)
"""
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    signals = detector.check_orphaned(
        tmp_path / "reviewers" / "security" / "KNOWLEDGE.md", "security"
    )
    assert len(signals) == 1
    assert signals[0].signal_type == "orphaned"
    assert signals[0].severity == "low"


def test_existing_file_not_orphaned(tmp_path: Path):
    """Path that exists on disk → no orphaned signal."""
    today = date.today().isoformat()
    ref_dir = tmp_path / "project" / "app"
    ref_dir.mkdir(parents=True)
    (ref_dir / "db.py").write_text("# db module\n")

    content = f"""## Patterns Found

- [{today}] Issue in `app/db.py:42` (Source: r1)
"""
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(
        reviewers_dir=tmp_path / "reviewers",
        project_root=tmp_path / "project",
    )
    signals = detector.check_orphaned(
        tmp_path / "reviewers" / "security" / "KNOWLEDGE.md", "security"
    )
    assert signals == []




def test_analyze_combines_all_checks(tmp_path: Path):
    """Full analysis runs all 4 checks."""
    old_date = (date.today() - timedelta(days=120)).isoformat()
    today = date.today().isoformat()
    content = f"""## Patterns Found

- [{old_date}] Old stale entry about `gone/file.py:1` (Source: r1)
- [{today}] Fresh entry about `app/db.py:42` (Source: r2)

## False Positives to Avoid

- [{today}] `app/db.py:42` is actually fine (Source: r3)
"""
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    report = detector.analyze()
    assert isinstance(report, DriftReport)
    signal_types = {s.signal_type for s in report.signals}
    assert "stale" in signal_types
    assert "contradictory" in signal_types
    assert "orphaned" in signal_types




def test_report_recommendation_healthy(tmp_path: Path):
    """No high signals → 'healthy'."""
    today = date.today().isoformat()
    content = f"""## Patterns Found

- [{today}] Everything is fine in `existing.py` (Source: r1)
"""
    (tmp_path / "project" / "existing.py").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "project" / "existing.py").write_text("# ok\n")

    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(
        reviewers_dir=tmp_path / "reviewers",
        project_root=tmp_path / "project",
    )
    report = detector.analyze()
    assert report.recommendation == "healthy"


def test_report_recommendation_needs_pruning(tmp_path: Path):
    """Bloat signal → 'needs_pruning'."""
    today = date.today().isoformat()
    lines = [f"- [{today}] Entry {i} (Source: test)" for i in range(55)]
    content = "## Patterns Found\n\n" + "\n".join(lines) + "\n"
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    report = detector.analyze()
    assert report.recommendation == "needs_pruning"


def test_report_recommendation_needs_review(tmp_path: Path):
    """Contradiction signal → 'needs_review'."""
    today = date.today().isoformat()
    content = f"""## Patterns Found

- [{today}] Bug in `app/x.py:1` (Source: r1)

## False Positives to Avoid

- [{today}] `app/x.py:1` is fine (Source: r2)
"""
    _make_reviewer_dir(tmp_path, "security", content)
    detector = DriftDetector(reviewers_dir=tmp_path / "reviewers")
    report = detector.analyze()
    assert report.recommendation == "needs_review"

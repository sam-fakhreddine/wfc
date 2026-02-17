"""Tests for the review CLI module.

TDD: Tests written first for TASK-011.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wfc.scripts.skills.review.cli import (
    build_parser,
    format_json_output,
    format_text_output,
    main,
)
from wfc.scripts.skills.review.consensus_score import ConsensusScoreResult, ScoredFinding
from wfc.scripts.skills.review.fingerprint import DeduplicatedFinding
from wfc.scripts.skills.review.orchestrator import ReviewResult


def _make_finding(
    file: str = "src/auth.py",
    line_start: int = 45,
    category: str = "validation",
    severity: float = 5.0,
    confidence: float = 7.0,
    k: int = 2,
) -> DeduplicatedFinding:
    """Helper to create a DeduplicatedFinding."""
    return DeduplicatedFinding(
        fingerprint="abc123",
        file=file,
        line_start=line_start,
        line_end=line_start + 5,
        category=category,
        severity=severity,
        confidence=confidence,
        description=f"Issue in {file}",
        descriptions=[f"Issue in {file}"],
        remediation=["Fix the issue"],
        reviewer_ids=["rev1", "rev2"][:k],
        k=k,
    )


def _make_scored_finding(
    file: str = "src/auth.py",
    line_start: int = 45,
    category: str = "validation",
    severity: float = 5.0,
    confidence: float = 7.0,
    k: int = 2,
    R_i: float = 3.5,
    tier: str = "informational",
) -> ScoredFinding:
    """Helper to create a ScoredFinding."""
    finding = _make_finding(file, line_start, category, severity, confidence, k)
    return ScoredFinding(finding=finding, R_i=R_i, tier=tier)


def _make_review_result(
    task_id: str = "TASK-001",
    passed: bool = True,
    cs: float = 3.50,
    tier: str = "informational",
    findings: list[ScoredFinding] | None = None,
) -> ReviewResult:
    """Helper to create a ReviewResult with a ConsensusScoreResult."""
    if findings is None:
        findings = [
            _make_scored_finding(
                file="src/auth.py",
                line_start=45,
                category="validation",
                severity=5.0,
                k=2,
                R_i=3.5,
                tier="informational",
            ),
            _make_scored_finding(
                file="src/utils.py",
                line_start=12,
                category="naming",
                severity=2.0,
                k=1,
                R_i=1.4,
                tier="informational",
            ),
        ]

    consensus = ConsensusScoreResult(
        cs=cs,
        tier=tier,
        findings=findings,
        R_bar=2.50,
        R_max=3.50,
        k_total=3,
        n=5,
        passed=passed,
        minority_protection_applied=False,
        summary=f"CS={cs:.2f} ({tier}): {len(findings)} finding(s), review {'passed' if passed else 'FAILED'}.",
    )

    return ReviewResult(
        task_id=task_id,
        consensus=consensus,
        report_path=Path("/tmp/REVIEW-TASK-001.md"),
        passed=passed,
    )


class TestBuildParser:
    """test_build_parser - Parser has all expected arguments."""

    def test_has_files_argument(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "b.py"])
        assert args.files == ["a.py", "b.py"]

    def test_has_diff_argument(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "--diff", "some diff"])
        assert args.diff == "some diff"

    def test_has_task_id_argument(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "--task-id", "MY-TASK"])
        assert args.task_id == "MY-TASK"

    def test_task_id_default(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py"])
        assert args.task_id == "REVIEW-001"

    def test_has_output_dir_argument(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "--output-dir", "/tmp/out"])
        assert args.output_dir == "/tmp/out"

    def test_has_format_argument(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "--format", "json"])
        assert args.format == "json"

    def test_format_default_is_text(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py"])
        assert args.format == "text"

    def test_format_choices(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--files", "a.py", "--format", "xml"])

    def test_has_emergency_bypass_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "--emergency-bypass", "--bypass-reason", "urgent"])
        assert args.emergency_bypass is True

    def test_has_bypass_reason(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "--bypass-reason", "hotfix"])
        assert args.bypass_reason == "hotfix"

    def test_has_bypassed_by(self):
        parser = build_parser()
        args = parser.parse_args(["--files", "a.py", "--bypassed-by", "alice"])
        assert args.bypassed_by == "alice"

    def test_files_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestFormatTextOutput:
    """test_format_text_output - Text format contains key info."""

    def test_contains_task_id(self):
        result = _make_review_result()
        text = format_text_output(result)
        assert "TASK-001" in text

    def test_contains_status_passed(self):
        result = _make_review_result(passed=True)
        text = format_text_output(result)
        assert "PASSED" in text

    def test_contains_status_failed(self):
        result = _make_review_result(passed=False, cs=8.0, tier="important")
        text = format_text_output(result)
        assert "FAILED" in text

    def test_contains_consensus_score(self):
        result = _make_review_result(cs=3.50)
        text = format_text_output(result)
        assert "CS=3.50" in text

    def test_contains_tier(self):
        result = _make_review_result(tier="informational")
        text = format_text_output(result)
        assert "informational" in text

    def test_contains_findings_count(self):
        result = _make_review_result()
        text = format_text_output(result)
        assert "Findings: 2" in text

    def test_contains_finding_details(self):
        result = _make_review_result()
        text = format_text_output(result)
        assert "src/auth.py:45" in text
        assert "validation" in text

    def test_contains_summary(self):
        result = _make_review_result()
        text = format_text_output(result)
        assert "Summary:" in text


class TestFormatJsonOutput:
    """test_format_json_output - JSON format is valid and contains all fields."""

    def test_valid_json(self):
        result = _make_review_result()
        output = format_json_output(result)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_contains_task_id(self):
        result = _make_review_result(task_id="TASK-001")
        data = json.loads(format_json_output(result))
        assert data["task_id"] == "TASK-001"

    def test_contains_passed(self):
        result = _make_review_result(passed=True)
        data = json.loads(format_json_output(result))
        assert data["passed"] is True

    def test_contains_cs(self):
        result = _make_review_result(cs=3.50)
        data = json.loads(format_json_output(result))
        assert data["cs"] == 3.50

    def test_contains_tier(self):
        result = _make_review_result(tier="informational")
        data = json.loads(format_json_output(result))
        assert data["tier"] == "informational"

    def test_contains_findings_count(self):
        result = _make_review_result()
        data = json.loads(format_json_output(result))
        assert data["findings_count"] == 2

    def test_contains_findings_list(self):
        result = _make_review_result()
        data = json.loads(format_json_output(result))
        assert isinstance(data["findings"], list)
        assert len(data["findings"]) == 2

    def test_contains_r_bar(self):
        result = _make_review_result()
        data = json.loads(format_json_output(result))
        assert "R_bar" in data

    def test_contains_r_max(self):
        result = _make_review_result()
        data = json.loads(format_json_output(result))
        assert "R_max" in data

    def test_contains_k_total(self):
        result = _make_review_result()
        data = json.loads(format_json_output(result))
        assert "k_total" in data

    def test_contains_minority_protection(self):
        result = _make_review_result()
        data = json.loads(format_json_output(result))
        assert "minority_protection_applied" in data

    def test_contains_summary(self):
        result = _make_review_result()
        data = json.loads(format_json_output(result))
        assert "summary" in data


class TestTextAndJsonSameInfo:
    """test_text_and_json_same_info - Both formats have same info (PROP-014)."""

    def test_same_task_id(self):
        result = _make_review_result(task_id="TASK-XYZ")
        text = format_text_output(result)
        data = json.loads(format_json_output(result))
        assert "TASK-XYZ" in text
        assert data["task_id"] == "TASK-XYZ"

    def test_same_cs(self):
        result = _make_review_result(cs=5.25)
        text = format_text_output(result)
        data = json.loads(format_json_output(result))
        assert "CS=5.25" in text
        assert data["cs"] == 5.25

    def test_same_passed_status(self):
        result = _make_review_result(passed=True)
        text = format_text_output(result)
        data = json.loads(format_json_output(result))
        assert "PASSED" in text
        assert data["passed"] is True

    def test_same_tier(self):
        result = _make_review_result(tier="moderate")
        text = format_text_output(result)
        data = json.loads(format_json_output(result))
        assert "moderate" in text
        assert data["tier"] == "moderate"

    def test_same_findings_count(self):
        result = _make_review_result()
        text = format_text_output(result)
        data = json.loads(format_json_output(result))
        assert "Findings: 2" in text
        assert data["findings_count"] == 2


class TestMainReturnsExitCode:
    """test_main_returns_0_on_pass and test_main_returns_1_on_fail."""

    @patch("wfc.scripts.skills.review.cli.ReviewOrchestrator")
    def test_main_returns_0_on_pass(self, mock_orch_cls):
        result = _make_review_result(passed=True)
        mock_orch = MagicMock()
        mock_orch.prepare_review.return_value = [{"task": "spec"}]
        mock_orch.finalize_review.return_value = result
        mock_orch_cls.return_value = mock_orch

        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main(["--files", "a.py", "--output-dir", tmpdir])

        assert exit_code == 0

    @patch("wfc.scripts.skills.review.cli.ReviewOrchestrator")
    def test_main_returns_1_on_fail(self, mock_orch_cls):
        result = _make_review_result(passed=False, cs=8.0, tier="important")
        mock_orch = MagicMock()
        mock_orch.prepare_review.return_value = [{"task": "spec"}]
        mock_orch.finalize_review.return_value = result
        mock_orch_cls.return_value = mock_orch

        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main(["--files", "a.py", "--output-dir", tmpdir])

        assert exit_code == 1


class TestDiffFromFile:
    """test_diff_from_file - --diff with file path reads the file."""

    @patch("wfc.scripts.skills.review.cli.ReviewOrchestrator")
    def test_diff_from_file(self, mock_orch_cls):
        result = _make_review_result(passed=True)
        mock_orch = MagicMock()
        mock_orch.prepare_review.return_value = [{"task": "spec"}]
        mock_orch.finalize_review.return_value = result
        mock_orch_cls.return_value = mock_orch

        with tempfile.TemporaryDirectory() as tmpdir:
            diff_file = Path(tmpdir) / "my.diff"
            diff_file.write_text("diff --git a/foo b/foo\n+new line\n")

            exit_code = main(["--files", "a.py", "--diff", str(diff_file), "--output-dir", tmpdir])

        call_args = mock_orch.prepare_review.call_args
        request = call_args[0][0]
        assert request.diff_content == "diff --git a/foo b/foo\n+new line\n"


class TestEmergencyBypass:
    """test_emergency_bypass_requires_reason."""

    def test_emergency_bypass_requires_reason(self):
        """--emergency-bypass without --bypass-reason should return error exit code."""
        exit_code = main(["--files", "a.py", "--emergency-bypass"])
        assert exit_code == 1

    @patch("wfc.scripts.skills.review.cli.ReviewOrchestrator")
    def test_emergency_bypass_with_reason_works(self, mock_orch_cls):
        result = _make_review_result(passed=True)
        mock_orch = MagicMock()
        mock_orch.prepare_review.return_value = [{"task": "spec"}]
        mock_orch.finalize_review.return_value = result
        mock_orch_cls.return_value = mock_orch

        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([
                "--files", "a.py",
                "--emergency-bypass",
                "--bypass-reason", "hotfix for prod",
                "--output-dir", tmpdir,
            ])

        assert exit_code == 0

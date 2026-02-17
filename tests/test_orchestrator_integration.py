"""
Integration tests for the rewritten ReviewOrchestrator.

Tests the full pipeline: ReviewerEngine -> Fingerprinter -> ConsensusScore -> Report.
TDD: Tests written FIRST, then implementation.
"""

import json
import textwrap
from pathlib import Path

import pytest

from wfc.scripts.skills.review.reviewer_loader import REVIEWER_IDS, ReviewerLoader
from wfc.scripts.skills.review.reviewer_engine import ReviewerEngine
from wfc.scripts.skills.review.orchestrator import (
    ReviewOrchestrator,
    ReviewRequest,
    ReviewResult,
)
from wfc.scripts.skills.review.consensus_score import ConsensusScoreResult


@pytest.fixture()
def reviewers_dir(tmp_path: Path) -> Path:
    """Create a temporary reviewers directory with all 5 reviewers."""
    for reviewer_id in REVIEWER_IDS:
        d = tmp_path / reviewer_id
        d.mkdir()

        prompt = textwrap.dedent(f"""\
            # {reviewer_id.title()} Reviewer Agent

            ## Identity

            You are the {reviewer_id} reviewer.

            ## Temperature

            0.4

            ## Output Format

            ```json
            {{"severity": "<1-10>", "description": "<what>"}}
            ```
        """)
        (d / "PROMPT.md").write_text(prompt, encoding="utf-8")

        knowledge = f"# KNOWLEDGE.md -- {reviewer_id.title()}\n\n- Known pattern.\n"
        (d / "KNOWLEDGE.md").write_text(knowledge, encoding="utf-8")

    return tmp_path


@pytest.fixture()
def engine(reviewers_dir: Path) -> ReviewerEngine:
    loader = ReviewerLoader(reviewers_dir=reviewers_dir)
    return ReviewerEngine(loader=loader)


@pytest.fixture()
def orchestrator(engine: ReviewerEngine) -> ReviewOrchestrator:
    return ReviewOrchestrator(reviewer_engine=engine)


@pytest.fixture()
def basic_request() -> ReviewRequest:
    return ReviewRequest(
        task_id="TASK-001",
        files=["src/main.py", "src/utils.py"],
        diff_content="+ def new_function():\n+     return 42",
    )


class TestPrepareReview:
    def test_prepare_review_returns_5_task_specs(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest
    ) -> None:
        """Engine produces 5 task specs."""
        tasks = orchestrator.prepare_review(basic_request)
        assert len(tasks) == 5
        task_ids = {t["reviewer_id"] for t in tasks}
        assert task_ids == set(REVIEWER_IDS)

    def test_prepare_review_includes_diff(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest
    ) -> None:
        """Task prompts include the diff content."""
        tasks = orchestrator.prepare_review(basic_request)
        for task in tasks:
            assert "new_function" in task["prompt"]

    def test_prepare_review_includes_properties(
        self, orchestrator: ReviewOrchestrator
    ) -> None:
        """Task prompts include properties when provided."""
        request = ReviewRequest(
            task_id="TASK-002",
            files=["app.py"],
            properties=[{"type": "SAFETY", "statement": "No SQL injection"}],
        )
        tasks = orchestrator.prepare_review(request)
        task = tasks[0]
        assert "SAFETY" in task["prompt"]


class TestFinalizeReview:
    def test_finalize_review_empty_responses(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest, tmp_path: Path
    ) -> None:
        """Empty responses (all clean) produce a passing result."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        responses = [
            {"reviewer_id": rid, "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."}
            for rid in REVIEWER_IDS
        ]

        result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert isinstance(result, ReviewResult)
        assert result.task_id == "TASK-001"
        assert result.passed is True
        assert isinstance(result.consensus, ConsensusScoreResult)
        assert result.consensus.cs == 0.0
        assert result.consensus.tier == "informational"

    def test_finalize_review_with_findings(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest, tmp_path: Path
    ) -> None:
        """Findings are deduplicated and scored."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        finding = json.dumps([{
            "severity": "5",
            "confidence": "6",
            "category": "naming",
            "file": "src/main.py",
            "line_start": "10",
            "line_end": "10",
            "description": "Bad variable name",
            "remediation": "Use descriptive name",
        }])

        responses = [
            {"reviewer_id": "security", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "correctness", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": f"{finding}\nSCORE: 6.0\nSUMMARY: Naming issues."},
            {"reviewer_id": "reliability", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
        ]

        result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert isinstance(result, ReviewResult)
        assert result.consensus.cs > 0.0
        assert len(result.consensus.findings) >= 1

    def test_finalize_review_generates_report(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest, tmp_path: Path
    ) -> None:
        """Report file is created with correct content."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        responses = [
            {"reviewer_id": rid, "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."}
            for rid in REVIEWER_IDS
        ]

        result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert result.report_path.exists()
        report_content = result.report_path.read_text()
        assert "TASK-001" in report_content
        assert "CS=" in report_content or "Consensus Score" in report_content
        assert "PASSED" in report_content or "passed" in report_content

    def test_finalize_review_high_severity_fails(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest, tmp_path: Path
    ) -> None:
        """Critical findings cause failure (CS >= 7.0 = important/critical tier)."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        critical_finding = json.dumps([{
            "severity": "9",
            "confidence": "9",
            "category": "injection",
            "file": "src/main.py",
            "line_start": "10",
            "line_end": "10",
            "description": "SQL injection vulnerability",
            "remediation": "Use parameterized queries",
        }])

        responses = [
            {"reviewer_id": "security", "response": f"{critical_finding}\nSCORE: 2.0\nSUMMARY: Critical issue."},
            {"reviewer_id": "correctness", "response": f"{critical_finding}\nSCORE: 3.0\nSUMMARY: Bug found."},
            {"reviewer_id": "performance", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": f"{critical_finding}\nSCORE: 2.0\nSUMMARY: Reliability risk."},
        ]

        result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert result.passed is False
        assert result.consensus.tier in ("important", "critical")

    def test_finalize_review_mpr_applied(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest, tmp_path: Path
    ) -> None:
        """Minority protection is triggered for high-severity security finding."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        critical_finding = json.dumps([{
            "severity": "10",
            "confidence": "10",
            "category": "rce",
            "file": "src/main.py",
            "line_start": "5",
            "line_end": "5",
            "description": "Remote code execution",
            "remediation": "Sanitize input",
        }])

        responses = [
            {"reviewer_id": "security", "response": f"{critical_finding}\nSCORE: 1.0\nSUMMARY: RCE found."},
            {"reviewer_id": "correctness", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
        ]

        result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert result.consensus.minority_protection_applied is True
        assert result.passed is False


class TestReviewRequest:
    def test_review_request_minimal(self) -> None:
        """ReviewRequest works with just task_id + files."""
        request = ReviewRequest(task_id="TASK-003", files=["main.py"])
        assert request.task_id == "TASK-003"
        assert request.files == ["main.py"]
        assert request.diff_content == ""
        assert request.properties == []

    def test_review_request_with_all_fields(self) -> None:
        """ReviewRequest works with all fields."""
        request = ReviewRequest(
            task_id="TASK-004",
            files=["app.py", "test_app.py"],
            diff_content="+ code",
            properties=[{"type": "SAFETY", "statement": "No crashes"}],
        )
        assert request.task_id == "TASK-004"
        assert len(request.files) == 2
        assert request.diff_content == "+ code"
        assert len(request.properties) == 1


class TestOutputPathValidation:
    def test_output_path_validation_rejects_relative(self) -> None:
        """Security validation rejects relative paths."""
        with pytest.raises(ValueError, match="absolute"):
            ReviewOrchestrator._validate_output_path(Path("relative/path"))

    def test_output_path_validation_rejects_sensitive_dirs(self) -> None:
        """Security validation rejects sensitive directories."""
        with pytest.raises(ValueError, match="sensitive"):
            ReviewOrchestrator._validate_output_path(Path("/etc/shadow"))

    def test_output_path_validation_rejects_ssh(self) -> None:
        """Security validation rejects .ssh directory."""
        with pytest.raises(ValueError, match="sensitive"):
            ReviewOrchestrator._validate_output_path(Path.home() / ".ssh" / "key")

    def test_output_path_validation_accepts_valid(self, tmp_path: Path) -> None:
        """Security validation accepts valid output paths."""
        valid_path = tmp_path / "output" / "report.md"
        ReviewOrchestrator._validate_output_path(valid_path)


class TestReviewResultDataclass:
    def test_review_result_fields(self, tmp_path: Path) -> None:
        """ReviewResult has expected fields."""
        cs_result = ConsensusScoreResult(
            cs=3.5,
            tier="informational",
            findings=[],
            R_bar=0.0,
            R_max=0.0,
            k_total=0,
            n=5,
            passed=True,
            minority_protection_applied=False,
            summary="CS=3.50 (informational): 0 findings, review passed.",
        )
        result = ReviewResult(
            task_id="TASK-005",
            consensus=cs_result,
            report_path=tmp_path / "report.md",
            passed=True,
        )
        assert result.task_id == "TASK-005"
        assert result.passed is True
        assert result.consensus.cs == 3.5


class TestDuplicateDeduplication:
    def test_duplicate_findings_across_reviewers_are_merged(
        self, orchestrator: ReviewOrchestrator, basic_request: ReviewRequest, tmp_path: Path
    ) -> None:
        """Same finding from multiple reviewers is deduplicated (k increases)."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        finding = json.dumps([{
            "severity": "7",
            "confidence": "8",
            "category": "validation",
            "file": "src/main.py",
            "line_start": "10",
            "line_end": "10",
            "description": "Missing input validation",
            "remediation": "Add validation",
        }])

        responses = [
            {"reviewer_id": "security", "response": f"{finding}\nSCORE: 5.0\nSUMMARY: Validation issue."},
            {"reviewer_id": "correctness", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": f"{finding}\nSCORE: 5.0\nSUMMARY: Validation issue."},
        ]

        result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert len(result.consensus.findings) == 1
        assert result.consensus.findings[0].finding.k == 2

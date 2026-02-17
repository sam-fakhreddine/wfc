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

        result = orchestrator.finalize_review(basic_request, responses, output_dir, skip_validation=True)

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

        result = orchestrator.finalize_review(basic_request, responses, output_dir, skip_validation=True)

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


# ---------------------------------------------------------------------------
# TASK-014: Model Routing Integration Tests
# ---------------------------------------------------------------------------

class TestModelRoutingInTaskSpecs:
    """Tests for TASK-014: Wire ModelRouter into prepare_review_tasks()."""

    def test_model_field_in_task_specs(
        self, engine: ReviewerEngine, reviewers_dir: Path
    ) -> None:
        """Each task spec has a model key when a ModelRouter is provided."""
        from wfc.scripts.skills.review.model_router import ModelRouter

        router = ModelRouter()
        tasks = engine.prepare_review_tasks(
            files=["src/main.py"],
            diff_content="+ def foo():\n+     pass",
            model_router=router,
        )
        assert len(tasks) == 5
        for task in tasks:
            reviewer = task.get("reviewer_id")
            assert "model" in task, f"Task spec for {reviewer} missing model key"
            assert task["model"], f"model field is empty for {reviewer}"

    def test_single_model_overrides_all(
        self, engine: ReviewerEngine, reviewers_dir: Path
    ) -> None:
        """With single_model set, all task specs use that model regardless of routing."""
        forced_model = "claude-haiku-4-5-20251001"
        tasks = engine.prepare_review_tasks(
            files=["src/main.py"],
            diff_content="+ x = 1",
            single_model=forced_model,
        )
        assert len(tasks) == 5
        for task in tasks:
            reviewer = task.get("reviewer_id")
            actual = task.get("model")
            assert actual == forced_model, (
                f"Expected {forced_model} but got {actual} for {reviewer}"
            )

    def test_no_router_uses_default_model_or_none(
        self, engine: ReviewerEngine, reviewers_dir: Path
    ) -> None:
        """Without router or single_model, task specs have no model key (backward compat)."""
        tasks = engine.prepare_review_tasks(
            files=["src/main.py"],
            diff_content="+ x = 1",
        )
        assert len(tasks) == 5
        for task in tasks:
            reviewer = task.get("reviewer_id")
            assert "model" not in task, (
                f"Task spec for {reviewer} should NOT have model "
                "when no router is provided"
            )

    def test_cost_in_report(
        self,
        orchestrator: ReviewOrchestrator,
        basic_request: ReviewRequest,
        tmp_path: Path,
        engine: ReviewerEngine,
        reviewers_dir: Path,
    ) -> None:
        """Review report contains a Cost section when ModelRouter is wired to orchestrator."""
        from wfc.scripts.skills.review.model_router import ModelRouter
        from wfc.scripts.skills.review.orchestrator import ReviewOrchestrator as RO

        router = ModelRouter()
        orch = RO(reviewer_engine=engine, model_router=router)

        output_dir = tmp_path / "cost_output"
        output_dir.mkdir()

        responses = [
            {"reviewer_id": rid, "response": "[]\nSCORE: 10.0\nSUMMARY: Clean."}
            for rid in REVIEWER_IDS
        ]

        result = orch.finalize_review(basic_request, responses, output_dir)

        report_content = result.report_path.read_text()
        assert "Cost" in report_content, (
            "Report should contain a Cost section when model_router is set."
        )




# ============================================================
# TASK-004: Validation Integration Tests
# ============================================================

class TestValidationWiredIntoPipeline:
    """Tests for FindingValidator wired into finalize_review() pipeline."""

    def _make_finding_response(self, reviewer_id, severity="5", confidence="6"):
        """Helper to build a response with one finding."""
        import json as _json
        finding = _json.dumps([{
            "severity": severity,
            "confidence": confidence,
            "category": "injection",
            "file": "src/main.py",
            "line_start": "10",
            "line_end": "10",
            "description": "SQL injection vulnerability",
            "remediation": "Use parameterized queries",
        }])
        newline = "\n"
        return {
            "reviewer_id": reviewer_id,
            "response": finding + newline + "SCORE: 5.0" + newline + "SUMMARY: Found issues.",
        }

    def test_validation_wired_after_dedup_before_cs(
        self,
        orchestrator: ReviewOrchestrator,
        basic_request: ReviewRequest,
        tmp_path: Path,
    ) -> None:
        """FindingValidator is called after dedup and before CS calculation."""
        from unittest.mock import patch
        from wfc.scripts.skills.review.finding_validator import FindingValidator

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        nl = "\n"
        responses = [
            self._make_finding_response("security"),
            {"reviewer_id": "correctness", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
        ]

        validator_call_count = {"count": 0}
        original_validate = FindingValidator.validate

        def tracking_validate(self_inner, finding, *args, **kwargs):
            validator_call_count["count"] += 1
            return original_validate(self_inner, finding, *args, **kwargs)

        with patch.object(FindingValidator, "validate", tracking_validate):
            result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert validator_call_count["count"] >= 1
        assert isinstance(result, ReviewResult)
        assert result.task_id == "TASK-001"

    def test_skip_validation_bypasses_validator(
        self,
        orchestrator: ReviewOrchestrator,
        basic_request: ReviewRequest,
        tmp_path: Path,
    ) -> None:
        """When skip_validation=True, FindingValidator is never called."""
        from unittest.mock import patch
        from wfc.scripts.skills.review.finding_validator import FindingValidator

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        nl = "\n"
        responses = [
            self._make_finding_response("security"),
            {"reviewer_id": "correctness", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
        ]

        validator_call_count = {"count": 0}
        original_validate = FindingValidator.validate

        def tracking_validate(self_inner, finding, *args, **kwargs):
            validator_call_count["count"] += 1
            return original_validate(self_inner, finding, *args, **kwargs)

        with patch.object(FindingValidator, "validate", tracking_validate):
            result = orchestrator.finalize_review(
                basic_request, responses, output_dir, skip_validation=True
            )

        assert validator_call_count["count"] == 0
        assert isinstance(result, ReviewResult)

    def test_historically_rejected_excluded_from_cs(
        self,
        orchestrator: ReviewOrchestrator,
        basic_request: ReviewRequest,
        tmp_path: Path,
    ) -> None:
        """HISTORICALLY_REJECTED findings are excluded from CS calculation entirely."""
        from unittest.mock import patch
        from wfc.scripts.skills.review.finding_validator import (
            FindingValidator,
            ValidatedFinding,
            ValidationStatus,
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        nl = "\n"
        responses = [
            self._make_finding_response("security", severity="9", confidence="9"),
            {"reviewer_id": "correctness", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
        ]

        def always_reject(self_inner, finding, *args, **kwargs):
            return ValidatedFinding(
                finding=finding,
                validation_status=ValidationStatus.HISTORICALLY_REJECTED,
                confidence=finding.confidence,
                validation_notes=["Historically rejected"],
                weight=0.0,
            )

        with patch.object(FindingValidator, "validate", always_reject):
            result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert result.consensus.cs == 0.0
        assert result.passed is True

    def test_validation_summary_in_report(
        self,
        orchestrator: ReviewOrchestrator,
        basic_request: ReviewRequest,
        tmp_path: Path,
    ) -> None:
        """Review report includes a Validation Summary section."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        nl = "\n"
        responses = [
            self._make_finding_response("security"),
            {"reviewer_id": "correctness", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
        ]

        result = orchestrator.finalize_review(basic_request, responses, output_dir)

        report_content = result.report_path.read_text()
        assert "Validation Summary" in report_content

    def test_validation_failure_does_not_block_review(
        self,
        orchestrator: ReviewOrchestrator,
        basic_request: ReviewRequest,
        tmp_path: Path,
    ) -> None:
        """Validator exceptions are caught (PROP-001 fail-open): review still completes."""
        from unittest.mock import patch
        from wfc.scripts.skills.review.finding_validator import FindingValidator

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        nl = "\n"
        responses = [
            self._make_finding_response("security"),
            {"reviewer_id": "correctness", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
        ]

        def always_raise(self_inner, finding, *args, **kwargs):
            raise RuntimeError("Simulated validator crash")

        with patch.object(FindingValidator, "validate", always_raise):
            result = orchestrator.finalize_review(basic_request, responses, output_dir)

        assert isinstance(result, ReviewResult)
        assert result.task_id == "TASK-001"

    def test_cs_weights_verified_higher_than_disputed(
        self,
        orchestrator: ReviewOrchestrator,
        basic_request: ReviewRequest,
        tmp_path: Path,
    ) -> None:
        """CS score for VERIFIED findings is higher than DISPUTED findings of same severity."""
        from unittest.mock import patch
        from wfc.scripts.skills.review.finding_validator import (
            FindingValidator,
            ValidatedFinding,
            ValidationStatus,
        )

        output_dir_verified = tmp_path / "output_verified"
        output_dir_verified.mkdir()

        output_dir_disputed = tmp_path / "output_disputed"
        output_dir_disputed.mkdir()

        nl = "\n"
        responses = [
            self._make_finding_response("security", severity="7", confidence="8"),
            {"reviewer_id": "correctness", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "performance", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "maintainability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
            {"reviewer_id": "reliability", "response": "[]" + nl + "SCORE: 10.0" + nl + "SUMMARY: Clean."},
        ]

        def always_verified(self_inner, finding, *args, **kwargs):
            return ValidatedFinding(
                finding=finding,
                validation_status=ValidationStatus.VERIFIED,
                confidence=finding.confidence,
                validation_notes=["Verified"],
                weight=1.0,
            )

        def always_disputed(self_inner, finding, *args, **kwargs):
            return ValidatedFinding(
                finding=finding,
                validation_status=ValidationStatus.DISPUTED,
                confidence=finding.confidence,
                validation_notes=["Disputed"],
                weight=0.2,
            )

        with patch.object(FindingValidator, "validate", always_verified):
            result_verified = orchestrator.finalize_review(
                basic_request, responses, output_dir_verified
            )

        with patch.object(FindingValidator, "validate", always_disputed):
            result_disputed = orchestrator.finalize_review(
                basic_request, responses, output_dir_disputed
            )

        assert result_verified.consensus.cs > result_disputed.consensus.cs


class TestConsensusScoreWeights:
    """Tests for ConsensusScore.calculate() with validation weight multipliers."""

    def _make_finding(
        self,
        file="src/main.py",
        line_start=10,
        category="injection",
        severity=7.0,
        confidence=8.0,
        reviewer_ids=None,
        k=1,
    ):
        from wfc.scripts.skills.review.fingerprint import DeduplicatedFinding, Fingerprinter

        fp = Fingerprinter().compute_fingerprint(file, line_start, category)
        return DeduplicatedFinding(
            fingerprint=fp,
            file=file,
            line_start=line_start,
            line_end=line_start,
            category=category,
            severity=severity,
            confidence=confidence,
            description="Test finding",
            descriptions=["Test finding"],
            remediation=["Fix it"],
            reviewer_ids=reviewer_ids or ["security"],
            k=k,
        )

    def test_calculate_with_weights_reduces_score_for_disputed(self) -> None:
        """CS with weight=0.2 (DISPUTED) is lower than CS with weight=1.0 (VERIFIED)."""
        from wfc.scripts.skills.review.consensus_score import ConsensusScore

        scorer = ConsensusScore()
        finding = self._make_finding(severity=7.0, confidence=8.0)

        result_no_weight = scorer.calculate([finding])
        result_disputed = scorer.calculate([finding], weights={finding.fingerprint: 0.2})

        assert result_disputed.cs < result_no_weight.cs

    def test_calculate_with_weight_one_equals_no_weight(self) -> None:
        """CS with weight=1.0 matches CS without weights."""
        from wfc.scripts.skills.review.consensus_score import ConsensusScore

        scorer = ConsensusScore()
        finding = self._make_finding(severity=5.0, confidence=6.0)

        result_no_weight = scorer.calculate([finding])
        result_full_weight = scorer.calculate([finding], weights={finding.fingerprint: 1.0})

        assert abs(result_no_weight.cs - result_full_weight.cs) < 1e-9

    def test_calculate_weight_zero_excludes_finding(self) -> None:
        """CS with weight=0.0 is equivalent to CS with no findings."""
        from wfc.scripts.skills.review.consensus_score import ConsensusScore

        scorer = ConsensusScore()
        finding = self._make_finding(severity=8.0, confidence=9.0)

        result_zero_weight = scorer.calculate([finding], weights={finding.fingerprint: 0.0})
        result_empty = scorer.calculate([])

        assert result_zero_weight.cs == result_empty.cs

    def test_calculate_missing_fingerprint_defaults_to_weight_one(self) -> None:
        """A finding without a matching weight entry defaults to weight=1.0."""
        from wfc.scripts.skills.review.consensus_score import ConsensusScore

        scorer = ConsensusScore()
        finding = self._make_finding(severity=5.0, confidence=6.0)

        result_no_weight = scorer.calculate([finding])
        result_partial_weight = scorer.calculate([finding], weights={"some_other_fp": 0.5})

        assert abs(result_no_weight.cs - result_partial_weight.cs) < 1e-9

    def test_calculate_mixed_weights_partial_exclusion(self) -> None:
        """Some findings at weight 0.2, others at 1.0: CS is between the extremes."""
        from wfc.scripts.skills.review.consensus_score import ConsensusScore

        scorer = ConsensusScore()
        finding_a = self._make_finding(line_start=10, severity=7.0, confidence=8.0)
        finding_b = self._make_finding(line_start=20, severity=7.0, confidence=8.0)

        all_findings = [finding_a, finding_b]
        result_no_weight = scorer.calculate(all_findings)
        result_mixed = scorer.calculate(
            all_findings,
            weights={finding_a.fingerprint: 0.2, finding_b.fingerprint: 1.0},
        )
        result_all_disputed = scorer.calculate(
            all_findings,
            weights={finding_a.fingerprint: 0.2, finding_b.fingerprint: 0.2},
        )

        assert result_mixed.cs > result_all_disputed.cs
        assert result_mixed.cs <= result_no_weight.cs

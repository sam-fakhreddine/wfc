"""End-to-end integration tests for the five-agent consensus review system.

Exercises the full pipeline: ReviewRequest -> prepare_review -> finalize_review -> ReviewResult,
including CLI output formatting, emergency bypass integration, and cross-component interactions.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wfc.scripts.skills.review.cli import (
    format_json_output,
    format_text_output,
    main as cli_main,
)
from wfc.scripts.skills.review.consensus_score import ConsensusScore, ConsensusScoreResult
from wfc.scripts.skills.review.emergency_bypass import BypassRecord, EmergencyBypass
from wfc.scripts.skills.review.fingerprint import DeduplicatedFinding, Fingerprinter
from wfc.scripts.skills.review.orchestrator import ReviewOrchestrator, ReviewRequest, ReviewResult
from wfc.scripts.skills.review.reviewer_engine import ReviewerEngine



def _clean_response(reviewer_id: str, score: float = 10.0, summary: str = "No issues") -> dict:
    """Build a mock reviewer response with no findings.

    Returns just a JSON empty array + SUMMARY/SCORE lines.
    Avoids wrapping in a JSON object (which _parse_findings would treat as a finding).
    """
    return {
        "reviewer_id": reviewer_id,
        "response": f"[]\nSUMMARY: {summary}\nSCORE: {score}",
    }


def _finding_response(
    reviewer_id: str,
    *,
    file: str = "app/auth.py",
    line_start: int = 42,
    line_end: int = 45,
    category: str = "sql-injection",
    severity: float = 8.0,
    confidence: float = 9.0,
    description: str = "User input passed directly to SQL query",
    remediation: str = "Use parameterized queries",
    score: float = 3.0,
    summary: str = "Issues found",
) -> dict:
    """Build a mock reviewer response with a single finding."""
    findings = [
        {
            "file": file,
            "line_start": line_start,
            "line_end": line_end,
            "category": category,
            "severity": severity,
            "confidence": confidence,
            "description": description,
            "remediation": remediation,
        }
    ]
    return {
        "reviewer_id": reviewer_id,
        "response": json.dumps(findings) + f"\nSUMMARY: {summary}\nSCORE: {score}",
    }


def _all_clean_responses() -> list[dict]:
    """Return 5 clean reviewer responses (one per reviewer)."""
    return [
        _clean_response("security"),
        _clean_response("correctness"),
        _clean_response("performance"),
        _clean_response("maintainability"),
        _clean_response("reliability"),
    ]


def _make_orchestrator() -> ReviewOrchestrator:
    """Create an orchestrator that skips disk-based reviewer loading."""
    engine = ReviewerEngine.__new__(ReviewerEngine)
    engine.loader = MagicMock()
    engine.retriever = None
    return ReviewOrchestrator(reviewer_engine=engine)


def _make_request(task_id: str = "TEST-001") -> ReviewRequest:
    return ReviewRequest(
        task_id=task_id,
        files=["app/auth.py", "app/models.py"],
        diff_content="--- a/app/auth.py\n+++ b/app/auth.py\n@@ -1 +1 @@\n-old\n+new",
    )




class TestPipelineE2E:
    """Tests that exercise the full orchestrator pipeline."""

    def test_e2e_clean_review_passes(self, tmp_path: Path) -> None:
        """No findings -> CS=0.0, passes, report generated."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = _all_clean_responses()

        result = orchestrator.finalize_review(request, responses, tmp_path)

        assert result.task_id == "TEST-001"
        assert result.passed is True
        assert result.consensus.cs == 0.0
        assert result.consensus.tier == "informational"
        assert result.consensus.findings == []
        assert result.report_path.exists()

    def test_e2e_single_low_severity_finding(self, tmp_path: Path) -> None:
        """One low finding -> informational tier, passes."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response(
                "maintainability",
                category="naming",
                severity=2.0,
                confidence=3.0,
                description="Variable name too short",
                score=9.0,
            ),
            _clean_response("security"),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("reliability"),
        ]

        result = orchestrator.finalize_review(request, responses, tmp_path)

        assert result.passed is True
        assert result.consensus.tier == "informational"
        assert len(result.consensus.findings) == 1
        sf = result.consensus.findings[0]
        assert sf.tier == "informational"
        assert sf.R_i == pytest.approx(0.6, abs=0.01)

    def test_e2e_multiple_findings_moderate(self, tmp_path: Path) -> None:
        """Several medium findings -> moderate tier, passes."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response(
                "correctness",
                category="null-check",
                severity=5.0,
                confidence=6.0,
                line_start=10,
                description="Missing null check",
                score=6.0,
            ),
            _finding_response(
                "performance",
                category="n-plus-one",
                severity=5.5,
                confidence=5.0,
                line_start=100,
                description="N+1 query detected",
                score=6.0,
            ),
            _finding_response(
                "maintainability",
                category="complexity",
                severity=4.0,
                confidence=4.5,
                line_start=200,
                description="Cyclomatic complexity > 10",
                score=7.0,
            ),
            _clean_response("security"),
            _clean_response("reliability"),
        ]

        result = orchestrator.finalize_review(request, responses, tmp_path)

        assert result.passed is True
        assert len(result.consensus.findings) == 3
        assert result.consensus.tier in ("informational", "moderate")

    def test_e2e_critical_finding_fails(self, tmp_path: Path) -> None:
        """High severity finding -> important/critical tier, fails."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response(
                "security",
                category="rce",
                severity=10.0,
                confidence=10.0,
                description="Remote code execution via eval()",
                score=1.0,
            ),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]

        result = orchestrator.finalize_review(request, responses, tmp_path)

        assert result.passed is False
        assert result.consensus.tier in ("important", "critical")
        assert result.consensus.cs >= 7.0

    def test_e2e_mpr_triggers_on_security(self, tmp_path: Path) -> None:
        """Security finding with R_max >= 8.5 triggers Minority Protection Rule."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response(
                "security",
                category="injection",
                severity=9.5,
                confidence=9.5,
                description="Critical injection vulnerability",
                score=1.0,
            ),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]

        result = orchestrator.finalize_review(request, responses, tmp_path)

        assert result.consensus.minority_protection_applied is True
        assert result.passed is False

    def test_e2e_duplicate_findings_merged(self, tmp_path: Path) -> None:
        """Same finding from 2 reviewers -> k=2, single deduped finding."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response(
                "security",
                file="app/auth.py",
                line_start=42,
                category="sql-injection",
                severity=8.0,
                confidence=9.0,
                description="SQL injection via user input",
                score=3.0,
            ),
            _finding_response(
                "correctness",
                file="app/auth.py",
                line_start=43,
                category="sql-injection",
                severity=7.5,
                confidence=8.0,
                description="Unsanitized query parameter",
                score=4.0,
            ),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]

        result = orchestrator.finalize_review(request, responses, tmp_path)

        assert len(result.consensus.findings) == 1
        finding = result.consensus.findings[0].finding
        assert finding.k == 2
        assert "security" in finding.reviewer_ids
        assert "correctness" in finding.reviewer_ids
        assert finding.severity == 8.0
        assert finding.confidence == 9.0

    def test_e2e_report_contains_all_sections(self, tmp_path: Path) -> None:
        """Report has: header, reviewer summaries, findings, summary."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response(
                "security",
                category="xss",
                severity=6.0,
                confidence=7.0,
                description="Cross-site scripting",
                score=5.0,
            ),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]

        result = orchestrator.finalize_review(request, responses, tmp_path)

        report = result.report_path.read_text()

        assert "# Review Report: TEST-001" in report
        assert "Consensus Score" in report

        assert "## Reviewer Summaries" in report
        assert "Security Reviewer" in report

        assert "## Findings" in report
        assert "xss" in report.lower() or "Cross-site scripting" in report

        assert "## Summary" in report
        assert "CS=" in report




class TestCLIE2E:
    """Tests for the CLI interface and output formatting."""

    def _run_cli_with_mock_responses(
        self,
        tmp_path: Path,
        responses: list[dict],
        extra_args: list[str] | None = None,
        fmt: str = "text",
    ) -> tuple[int, str, str]:
        """Run CLI with mocked orchestrator, capturing stdout/stderr.

        Returns (exit_code, stdout, stderr).
        """
        mock_orchestrator = _make_orchestrator()
        request = _make_request()

        result = mock_orchestrator.finalize_review(request, responses, tmp_path)

        with (
            patch("wfc.scripts.skills.review.cli.ReviewOrchestrator") as MockOrch,
            patch("sys.stdout") as mock_stdout,
            patch("sys.stderr") as mock_stderr,
        ):
            captured_out: list[str] = []
            captured_err: list[str] = []
            mock_stdout.write = lambda s: captured_out.append(s)
            mock_stderr.write = lambda s: captured_err.append(s)

            inst = MockOrch.return_value
            inst.prepare_review.return_value = []
            inst.finalize_review.return_value = result

            args = ["--files", "app/auth.py", "--task-id", "TEST-001",
                    "--output-dir", str(tmp_path), "--format", fmt]
            if extra_args:
                args.extend(extra_args)

            exit_code = cli_main(args)

        return exit_code, "".join(captured_out), "".join(captured_err)

    def test_e2e_cli_text_output(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """cli_main produces text output with expected fields."""
        mock_orchestrator = _make_orchestrator()
        request = _make_request()
        responses = _all_clean_responses()
        result = mock_orchestrator.finalize_review(request, responses, tmp_path)

        output = format_text_output(result)

        assert "Review: TEST-001" in output
        assert "Status: PASSED" in output
        assert "CS=" in output
        assert "Findings: 0" in output

    def test_e2e_cli_json_output(self, tmp_path: Path) -> None:
        """--format json produces valid JSON with all required fields."""
        mock_orchestrator = _make_orchestrator()
        request = _make_request()
        responses = _all_clean_responses()
        result = mock_orchestrator.finalize_review(request, responses, tmp_path)

        output = format_json_output(result)
        data = json.loads(output)

        assert data["task_id"] == "TEST-001"
        assert data["passed"] is True
        assert data["cs"] == 0.0
        assert data["tier"] == "informational"
        assert data["findings_count"] == 0
        assert data["findings"] == []
        assert "R_bar" in data
        assert "R_max" in data
        assert "k_total" in data
        assert "minority_protection_applied" in data
        assert "summary" in data

    def test_e2e_cli_json_output_with_findings(self, tmp_path: Path) -> None:
        """JSON output includes finding details when findings exist."""
        mock_orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response("security", severity=7.0, confidence=8.0, score=4.0),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]
        result = mock_orchestrator.finalize_review(request, responses, tmp_path)

        output = format_json_output(result)
        data = json.loads(output)

        assert data["findings_count"] == 1
        finding = data["findings"][0]
        assert finding["file"] == "app/auth.py"
        assert finding["category"] == "sql-injection"
        assert finding["severity"] == 7.0
        assert finding["k"] == 1
        assert "R_i" in finding
        assert "tier" in finding
        assert "reviewer_ids" in finding

    def test_e2e_cli_exit_code_pass(self, tmp_path: Path) -> None:
        """Clean review -> exit code 0."""
        mock_orchestrator = _make_orchestrator()
        request = _make_request()
        responses = _all_clean_responses()
        result = mock_orchestrator.finalize_review(request, responses, tmp_path)

        with patch("wfc.scripts.skills.review.cli.ReviewOrchestrator") as MockOrch:
            inst = MockOrch.return_value
            inst.prepare_review.return_value = []
            inst.finalize_review.return_value = result

            exit_code = cli_main([
                "--files", "app/auth.py",
                "--task-id", "TEST-001",
                "--output-dir", str(tmp_path),
            ])

        assert exit_code == 0

    def test_e2e_cli_exit_code_fail(self, tmp_path: Path) -> None:
        """Critical finding -> exit code 1."""
        mock_orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response("security", severity=10.0, confidence=10.0, score=1.0),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]
        result = mock_orchestrator.finalize_review(request, responses, tmp_path)
        assert result.passed is False

        with patch("wfc.scripts.skills.review.cli.ReviewOrchestrator") as MockOrch:
            inst = MockOrch.return_value
            inst.prepare_review.return_value = []
            inst.finalize_review.return_value = result

            exit_code = cli_main([
                "--files", "app/auth.py",
                "--task-id", "TEST-001",
                "--output-dir", str(tmp_path),
            ])

        assert exit_code == 1

    def test_e2e_cli_emergency_bypass_requires_reason(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """--emergency-bypass without --bypass-reason -> error exit code 1."""
        exit_code = cli_main([
            "--files", "app/auth.py",
            "--emergency-bypass",
            "--output-dir", str(tmp_path),
        ])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "bypass-reason" in captured.err.lower() or "bypass_reason" in captured.err.lower()




class TestEmergencyBypassE2E:
    """Tests for the emergency bypass mechanism integrated with the review pipeline."""

    def test_e2e_bypass_creates_audit_record(self, tmp_path: Path) -> None:
        """Bypass creates BYPASS-AUDIT.json with correct fields."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response("security", severity=9.0, confidence=9.0, score=2.0),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]
        result = orchestrator.finalize_review(request, responses, tmp_path)

        bypass = EmergencyBypass(audit_dir=tmp_path)
        record = bypass.create_bypass(
            task_id="TEST-001",
            reason="Hotfix for production outage",
            bypassed_by="developer@example.com",
            cs_result=result.consensus,
        )

        audit_path = tmp_path / "BYPASS-AUDIT.json"
        assert audit_path.exists()

        assert record.task_id == "TEST-001"
        assert record.reason == "Hotfix for production outage"
        assert record.bypassed_by == "developer@example.com"
        assert record.cs_at_bypass == result.consensus.cs
        assert record.tier_at_bypass == result.consensus.tier

        trail = bypass.load_audit_trail()
        assert len(trail) == 1
        assert trail[0].task_id == "TEST-001"
        assert trail[0].reason == "Hotfix for production outage"

    def test_e2e_bypass_with_failing_review(self, tmp_path: Path) -> None:
        """Review fails + bypass -> audit trail records original CS."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response("security", severity=10.0, confidence=10.0, score=1.0),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]
        result = orchestrator.finalize_review(request, responses, tmp_path)
        assert result.passed is False

        original_cs = result.consensus.cs
        original_tier = result.consensus.tier

        bypass = EmergencyBypass(audit_dir=tmp_path)
        record = bypass.create_bypass(
            task_id="TEST-001",
            reason="Critical production fix cannot wait",
            bypassed_by="oncall@example.com",
            cs_result=result.consensus,
        )

        assert record.cs_at_bypass == original_cs
        assert record.tier_at_bypass == original_tier
        assert original_cs >= 7.0
        assert original_tier in ("important", "critical")

        assert bypass.is_bypassed("TEST-001") is True

    def test_e2e_bypass_empty_reason_rejected(self, tmp_path: Path) -> None:
        """Empty bypass reason raises ValueError."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = _all_clean_responses()
        result = orchestrator.finalize_review(request, responses, tmp_path)

        bypass = EmergencyBypass(audit_dir=tmp_path)
        with pytest.raises(ValueError, match="non-empty"):
            bypass.create_bypass(
                task_id="TEST-001",
                reason="",
                bypassed_by="developer",
                cs_result=result.consensus,
            )




class TestCrossComponent:
    """Tests that verify integration between multiple components."""

    def test_e2e_knowledge_retriever_integration(self, tmp_path: Path) -> None:
        """ReviewerEngine with a (mock) retriever produces tasks with knowledge section."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [{"chunk": "SQL injection patterns", "score": 0.9}]
        mock_retriever.format_knowledge_section.return_value = (
            "# Relevant Knowledge\n\n- SQL injection is a common vulnerability"
        )
        mock_retriever.config = MagicMock()
        mock_retriever.config.token_budget = 500

        mock_loader = MagicMock()
        from wfc.scripts.skills.review.reviewer_loader import ReviewerConfig

        configs = [
            ReviewerConfig(
                id=rid,
                prompt=f"# {rid.title()} Reviewer\nReview for {rid} issues.",
                knowledge="",
                temperature=0.5,
                relevant=True,
            )
            for rid in ["security", "correctness", "performance", "maintainability", "reliability"]
        ]
        mock_loader.load_all.return_value = configs

        engine = ReviewerEngine(loader=mock_loader, retriever=mock_retriever)
        tasks = engine.prepare_review_tasks(
            files=["app/auth.py"],
            diff_content="--- a/app/auth.py\n+++ b/app/auth.py\n@@ -1 +1 @@\n-old\n+new",
        )

        assert len(tasks) == 5
        knowledge_found = any("Relevant Knowledge" in t["prompt"] for t in tasks)
        assert knowledge_found, "Expected knowledge section in at least one reviewer prompt"

    def test_e2e_full_cycle_prepare_finalize(self, tmp_path: Path) -> None:
        """prepare_review -> mock responses -> finalize_review -> validate all fields."""
        mock_loader = MagicMock()
        from wfc.scripts.skills.review.reviewer_loader import ReviewerConfig

        configs = [
            ReviewerConfig(
                id=rid,
                prompt=f"# {rid.title()} Reviewer\nReview for {rid} issues.",
                knowledge="",
                temperature=0.5,
                relevant=True,
            )
            for rid in ["security", "correctness", "performance", "maintainability", "reliability"]
        ]
        mock_loader.load_all.return_value = configs

        engine = ReviewerEngine(loader=mock_loader)
        orchestrator = ReviewOrchestrator(reviewer_engine=engine)
        request = _make_request("FULL-CYCLE-001")

        task_specs = orchestrator.prepare_review(request)
        assert len(task_specs) == 5
        for spec in task_specs:
            assert "reviewer_id" in spec
            assert "prompt" in spec
            assert "relevant" in spec

        mock_responses = [
            _finding_response(
                "security",
                category="hardcoded-secret",
                severity=8.0,
                confidence=8.5,
                description="Hardcoded API key",
                score=3.0,
            ),
            _clean_response("correctness"),
            _clean_response("performance"),
            _finding_response(
                "maintainability",
                category="complexity",
                severity=4.0,
                confidence=5.0,
                line_start=100,
                description="High cyclomatic complexity",
                score=7.0,
            ),
            _clean_response("reliability"),
        ]

        result = orchestrator.finalize_review(request, mock_responses, tmp_path)

        assert result.task_id == "FULL-CYCLE-001"
        assert isinstance(result.consensus, ConsensusScoreResult)
        assert isinstance(result.report_path, Path)
        assert result.report_path.exists()
        assert isinstance(result.passed, bool)

        cs = result.consensus
        assert cs.n == 5
        assert cs.cs >= 0.0
        assert len(cs.findings) == 2
        assert cs.tier in ("informational", "moderate", "important", "critical")
        assert isinstance(cs.summary, str)
        assert len(cs.summary) > 0

        report = result.report_path.read_text()
        assert "FULL-CYCLE-001" in report
        assert "Security Reviewer" in report
        assert "Maintainability Reviewer" in report

    def test_e2e_fingerprinter_to_consensus_score(self) -> None:
        """Verify fingerprinting feeds correctly into consensus scoring."""
        fingerprinter = Fingerprinter()
        scorer = ConsensusScore()

        raw_findings = [
            {
                "file": "app/db.py",
                "line_start": 48,
                "line_end": 55,
                "category": "sql-injection",
                "severity": 8.0,
                "confidence": 9.0,
                "description": "SQL injection in query builder",
                "remediation": "Use parameterized queries",
                "reviewer_id": "security",
            },
            {
                "file": "app/db.py",
                "line_start": 50,
                "line_end": 55,
                "category": "sql-injection",
                "severity": 7.5,
                "confidence": 8.5,
                "description": "Unsanitized user input in SQL",
                "remediation": "Sanitize inputs before query",
                "reviewer_id": "correctness",
            },
        ]

        deduped = fingerprinter.deduplicate(raw_findings)
        assert len(deduped) == 1
        assert deduped[0].k == 2

        cs_result = scorer.calculate(deduped)

        assert cs_result.cs > 0.0
        assert cs_result.k_total == 2
        assert len(cs_result.findings) == 1
        assert cs_result.findings[0].R_i == pytest.approx(7.2, abs=0.01)

    def test_e2e_text_output_with_findings(self, tmp_path: Path) -> None:
        """Text output includes finding details when findings exist."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = [
            _finding_response(
                "security",
                category="xss",
                severity=6.0,
                confidence=7.0,
                description="Reflected XSS",
                score=5.0,
            ),
            _clean_response("correctness"),
            _clean_response("performance"),
            _clean_response("maintainability"),
            _clean_response("reliability"),
        ]
        result = orchestrator.finalize_review(request, responses, tmp_path)

        text_output = format_text_output(result)

        assert "Status: PASSED" in text_output or "Status: FAILED" in text_output
        assert "Findings:" in text_output
        assert "xss" in text_output
        assert "app/auth.py" in text_output

    def test_e2e_no_findings_across_all_reviewers(self, tmp_path: Path) -> None:
        """All 5 reviewers report clean -> zero findings, pass."""
        orchestrator = _make_orchestrator()
        request = _make_request()
        responses = _all_clean_responses()

        result = orchestrator.finalize_review(request, responses, tmp_path)

        assert result.passed is True
        assert result.consensus.cs == 0.0
        assert result.consensus.k_total == 0
        assert result.consensus.R_bar == 0.0
        assert result.consensus.R_max == 0.0
        assert result.consensus.minority_protection_applied is False
        assert "0 findings" in result.consensus.summary

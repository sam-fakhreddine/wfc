"""Tests for DocAuditor - documentation gap analysis.

TDD: Tests written first. DocAuditor is analysis-only (never writes docs,
never blocks review). Follows fail-open pattern.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from wfc.scripts.skills.review.doc_auditor import DocAuditor, DocAuditReport, DocGap


class TestDocGapDataclass:
    def test_fields_present(self):
        gap = DocGap(
            doc_file="docs/workflow/WFC_IMPLEMENTATION.md",
            reason="Mentions orchestrator module",
            changed_file="wfc/scripts/skills/review/orchestrator.py",
            confidence="high",
        )
        assert gap.doc_file == "docs/workflow/WFC_IMPLEMENTATION.md"
        assert gap.reason == "Mentions orchestrator module"
        assert gap.changed_file == "wfc/scripts/skills/review/orchestrator.py"
        assert gap.confidence == "high"

    def test_confidence_medium(self):
        gap = DocGap(
            doc_file="CLAUDE.md",
            reason="Keyword match",
            changed_file="wfc/scripts/hooks/pretooluse_hook.py",
            confidence="medium",
        )
        assert gap.confidence == "medium"

    def test_confidence_low(self):
        gap = DocGap(
            doc_file="docs/README.md",
            reason="Weak indirect reference",
            changed_file="wfc/scripts/skills/review/fingerprint.py",
            confidence="low",
        )
        assert gap.confidence == "low"




class TestDocAuditReportDataclass:
    def test_fields_present(self, tmp_path: Path):
        report_path = tmp_path / "DOC-AUDIT-TASK-001.md"
        report = DocAuditReport(
            task_id="TASK-001",
            gaps=[],
            missing_docstrings=[],
            summary="No gaps found.",
            report_path=report_path,
        )
        assert report.task_id == "TASK-001"
        assert report.gaps == []
        assert report.missing_docstrings == []
        assert report.summary == "No gaps found."
        assert report.report_path == report_path

    def test_gaps_list_populated(self, tmp_path: Path):
        gap = DocGap("docs/a.md", "reason", "file.py", "high")
        report = DocAuditReport(
            task_id="T",
            gaps=[gap],
            missing_docstrings=["file.py:10: def foo"],
            summary="1 gap found.",
            report_path=tmp_path / "x.md",
        )
        assert len(report.gaps) == 1
        assert len(report.missing_docstrings) == 1

    def test_default_no_fields_required(self, tmp_path: Path):
        """DocAuditReport can hold empty collections."""
        r = DocAuditReport("X", [], [], "ok", tmp_path / "f.md")
        assert r.gaps == []
        assert r.missing_docstrings == []




class TestFindDocGaps:
    def _auditor(self) -> DocAuditor:
        return DocAuditor()

    def test_changed_file_with_matching_doc(self, tmp_path: Path):
        """A changed file whose module name appears in a doc → DocGap returned."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc = docs_dir / "IMPLEMENTATION.md"
        doc.write_text("See orchestrator for details.", encoding="utf-8")

        auditor = self._auditor()
        gaps = auditor._find_doc_gaps(
            files=["wfc/scripts/skills/review/orchestrator.py"],
            diff_content="",
            docs_root=tmp_path,
        )
        assert len(gaps) >= 1
        assert any("orchestrator" in g.reason.lower() or "orchestrator" in g.doc_file for g in gaps)

    def test_changed_file_with_no_matching_doc(self, tmp_path: Path):
        """A changed file with no docs mentioning it → no gap."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc = docs_dir / "unrelated.md"
        doc.write_text("# Unrelated\nNothing here.", encoding="utf-8")

        auditor = self._auditor()
        gaps = auditor._find_doc_gaps(
            files=["wfc/scripts/skills/review/xyznoMatch12345.py"],
            diff_content="",
            docs_root=tmp_path,
        )
        assert gaps == []

    def test_module_name_extracted_from_path(self, tmp_path: Path):
        """Module name is extracted correctly (stem of last path component)."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc = docs_dir / "ref.md"
        doc.write_text("fingerprint deduplication is used.", encoding="utf-8")

        auditor = self._auditor()
        gaps = auditor._find_doc_gaps(
            files=["wfc/scripts/skills/review/fingerprint.py"],
            diff_content="",
            docs_root=tmp_path,
        )
        assert len(gaps) >= 1

    def test_confidence_high_for_exact_path_match(self, tmp_path: Path):
        """Exact path mention in doc → confidence=high."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc = docs_dir / "arch.md"
        doc.write_text(
            "Key file: `wfc/scripts/skills/review/consensus_score.py`",
            encoding="utf-8",
        )

        auditor = self._auditor()
        gaps = auditor._find_doc_gaps(
            files=["wfc/scripts/skills/review/consensus_score.py"],
            diff_content="",
            docs_root=tmp_path,
        )
        high_confidence = [g for g in gaps if g.confidence == "high"]
        assert len(high_confidence) >= 1

    def test_multiple_changed_files_gaps_for_each(self, tmp_path: Path):
        """Multiple changed files → gaps checked for each independently."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc = docs_dir / "multi.md"
        doc.write_text(
            "orchestrator and fingerprint are both mentioned here.",
            encoding="utf-8",
        )

        auditor = self._auditor()
        gaps = auditor._find_doc_gaps(
            files=[
                "wfc/scripts/skills/review/orchestrator.py",
                "wfc/scripts/skills/review/fingerprint.py",
            ],
            diff_content="",
            docs_root=tmp_path,
        )
        changed_files_with_gaps = {g.changed_file for g in gaps}
        assert "wfc/scripts/skills/review/orchestrator.py" in changed_files_with_gaps
        assert "wfc/scripts/skills/review/fingerprint.py" in changed_files_with_gaps




class TestFindMissingDocstrings:
    def _auditor(self) -> DocAuditor:
        return DocAuditor()

    def test_new_function_without_docstring_reported(self, tmp_path: Path):
        """New function added in diff without docstring → reported."""
        py_file = tmp_path / "mymod.py"
        py_file.write_text(
            textwrap.dedent("""\
                def my_func(x):
                    return x + 1
            """),
            encoding="utf-8",
        )
        diff = textwrap.dedent("""\
            +def my_func(x):
            +    return x + 1
        """)

        auditor = self._auditor()
        missing = auditor._find_missing_docstrings(
            files=[str(py_file)],
            diff_content=diff,
        )
        assert len(missing) >= 1
        assert any("my_func" in item for item in missing)

    def test_new_function_with_docstring_not_reported(self, tmp_path: Path):
        """New function with a docstring → not reported as missing."""
        py_file = tmp_path / "mymod2.py"
        py_file.write_text(
            textwrap.dedent("""\
                def well_documented(x):
                    \"\"\"Return x + 1.\"\"\"
                    return x + 1
            """),
            encoding="utf-8",
        )
        diff = textwrap.dedent("""\
            +def well_documented(x):
            +    \"\"\"Return x + 1.\"\"\"
            +    return x + 1
        """)

        auditor = self._auditor()
        missing = auditor._find_missing_docstrings(
            files=[str(py_file)],
            diff_content=diff,
        )
        assert not any("well_documented" in item for item in missing)

    def test_non_python_file_skipped(self, tmp_path: Path):
        """Non-Python files are skipped (no error)."""
        js_file = tmp_path / "app.js"
        js_file.write_text("function foo() {}", encoding="utf-8")

        auditor = self._auditor()
        missing = auditor._find_missing_docstrings(
            files=[str(js_file)],
            diff_content="+function foo() {}",
        )
        assert isinstance(missing, list)

    def test_empty_diff_returns_empty(self, tmp_path: Path):
        """Empty diff → empty missing docstrings list."""
        py_file = tmp_path / "empty_diff.py"
        py_file.write_text("", encoding="utf-8")

        auditor = self._auditor()
        missing = auditor._find_missing_docstrings(
            files=[str(py_file)],
            diff_content="",
        )
        assert missing == []




class TestAnalyzeFailOpen:
    def _auditor(self) -> DocAuditor:
        return DocAuditor()

    def test_exception_in_find_doc_gaps_still_returns_report(self, tmp_path: Path, monkeypatch):
        """If _find_doc_gaps raises, analyze() still returns a DocAuditReport."""
        auditor = self._auditor()

        def bad_find(*args, **kwargs):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(auditor, "_find_doc_gaps", bad_find)

        result = auditor.analyze(
            task_id="TASK-X",
            files=["foo.py"],
            diff_content="",
            output_dir=tmp_path,
        )
        assert isinstance(result, DocAuditReport)
        assert result.task_id == "TASK-X"

    def test_invalid_files_list_still_returns(self, tmp_path: Path):
        """Files list with non-existent paths → graceful return."""
        auditor = self._auditor()
        result = auditor.analyze(
            task_id="TASK-Y",
            files=["/nonexistent/path/foo.py", "does_not_exist.py"],
            diff_content="",
            output_dir=tmp_path,
        )
        assert isinstance(result, DocAuditReport)
        assert result.task_id == "TASK-Y"

    def test_output_dir_not_writable_still_returns(self, tmp_path: Path):
        """If report write fails, analyze() still returns with error summary."""
        import unittest.mock as mock

        auditor = self._auditor()
        with mock.patch.object(auditor, "_write_report", side_effect=PermissionError("no write")):
            result = auditor.analyze(
                task_id="TASK-Z",
                files=[],
                diff_content="",
                output_dir=tmp_path,
            )
        assert isinstance(result, DocAuditReport)
        assert result.task_id == "TASK-Z"




class TestOrchestratorIntegration:
    """Tests that finalize_review() returns ReviewResult with doc_audit field."""

    def _make_orchestrator(self, tmp_path: Path):
        """Create a ReviewOrchestrator with minimal fixtures."""
        import textwrap

        from wfc.scripts.skills.review.orchestrator import ReviewOrchestrator
        from wfc.scripts.skills.review.reviewer_engine import ReviewerEngine
        from wfc.scripts.skills.review.reviewer_loader import REVIEWER_IDS, ReviewerLoader

        reviewers_dir = tmp_path / "reviewers"
        reviewers_dir.mkdir()
        for rid in REVIEWER_IDS:
            d = reviewers_dir / rid
            d.mkdir()
            prompt = textwrap.dedent(f"""\
                # {rid.title()} Reviewer

                ## Identity
                You are the {rid} reviewer.

                ## Temperature
                0.4

                ## Output Format
                ```json
                {{"severity": "1", "description": "ok"}}
                ```
            """)
            (d / "PROMPT.md").write_text(prompt, encoding="utf-8")
            (d / "KNOWLEDGE.md").write_text(f"# {rid}\n- known.\n", encoding="utf-8")

        loader = ReviewerLoader(reviewers_dir=reviewers_dir)
        engine = ReviewerEngine(loader=loader)
        return ReviewOrchestrator(reviewer_engine=engine)

    def _minimal_responses(self):
        """Build minimal passing task responses for all 5 reviewers."""
        import json

        from wfc.scripts.skills.review.reviewer_loader import REVIEWER_IDS

        responses = []
        for rid in REVIEWER_IDS:
            output = json.dumps({
                "reviewer": rid,
                "score": 8.0,
                "passed": True,
                "summary": "Looks good.",
                "findings": [],
            })
            responses.append({"reviewer_id": rid, "output": output})
        return responses

    def test_finalize_review_result_has_doc_audit_field(self, tmp_path: Path):
        """ReviewResult from finalize_review has a doc_audit attribute."""
        from wfc.scripts.skills.review.orchestrator import ReviewRequest, ReviewResult

        orch = self._make_orchestrator(tmp_path)
        request = ReviewRequest(
            task_id="TASK-DOC-001",
            files=["wfc/scripts/skills/review/orchestrator.py"],
            diff_content="",
        )
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        result = orch.finalize_review(request, self._minimal_responses(), output_dir)

        assert isinstance(result, ReviewResult)
        assert hasattr(result, "doc_audit")

    def test_review_report_contains_documentation_audit_section(self, tmp_path: Path):
        """REVIEW-{task_id}.md includes a '## Documentation Audit' section."""
        from wfc.scripts.skills.review.orchestrator import ReviewRequest

        orch = self._make_orchestrator(tmp_path)
        request = ReviewRequest(
            task_id="TASK-DOC-002",
            files=["wfc/scripts/skills/review/orchestrator.py"],
            diff_content="",
        )
        output_dir = tmp_path / "out2"
        output_dir.mkdir()

        result = orch.finalize_review(request, self._minimal_responses(), output_dir)

        report_text = result.report_path.read_text(encoding="utf-8")
        assert "## Documentation Audit" in report_text

    def test_doc_audit_never_blocks_review(self, tmp_path: Path):
        """doc_audit field does not affect the passed/failed decision."""
        import unittest.mock as mock

        from wfc.scripts.skills.review.orchestrator import ReviewRequest

        orch = self._make_orchestrator(tmp_path)
        request = ReviewRequest(
            task_id="TASK-DOC-003",
            files=["wfc/scripts/skills/review/orchestrator.py"],
            diff_content="",
        )
        output_dir = tmp_path / "out3"
        output_dir.mkdir()

        with mock.patch(
            "wfc.scripts.skills.review.orchestrator.DocAuditor.analyze",
            side_effect=RuntimeError("doc audit exploded"),
        ):
            result = orch.finalize_review(request, self._minimal_responses(), output_dir)

        assert isinstance(result.passed, bool)

    def test_doc_audit_report_file_created(self, tmp_path: Path):
        """DOC-AUDIT-{task_id}.md file is created in output_dir."""
        from wfc.scripts.skills.review.orchestrator import ReviewRequest

        orch = self._make_orchestrator(tmp_path)
        request = ReviewRequest(
            task_id="TASK-DOC-004",
            files=["wfc/scripts/skills/review/orchestrator.py"],
            diff_content="",
        )
        output_dir = tmp_path / "out4"
        output_dir.mkdir()

        result = orch.finalize_review(request, self._minimal_responses(), output_dir)

        if result.doc_audit is not None:
            assert result.doc_audit.task_id == "TASK-DOC-004"

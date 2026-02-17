"""Tests for FindingValidator - TDD (tests written before implementation).

Covers three validation layers:
  TASK-001: Structural Verification (file existence, real code lines)
  TASK-002: LLM Cross-Check (Haiku task spec, YES/NO response parsing)
  TASK-003: Historical Pattern Match (knowledge retriever integration)

PROP-001: fail-open - all exceptions are swallowed; finding keeps current state.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wfc.scripts.skills.review.finding_validator import (
    FindingValidator,
    ValidatedFinding,
    ValidationStatus,
)
from wfc.scripts.skills.review.fingerprint import DeduplicatedFinding


def _make_finding(
    file: str = "src/app.py",
    line_start: int = 10,
    line_end: int = 12,
    category: str = "injection",
    severity: float = 7.0,
    confidence: float = 8.0,
    description: str = "SQL injection risk",
) -> DeduplicatedFinding:
    return DeduplicatedFinding(
        fingerprint="abc123",
        file=file,
        line_start=line_start,
        line_end=line_end,
        category=category,
        severity=severity,
        confidence=confidence,
        description=description,
        descriptions=[description],
        remediation=["Use parameterized queries"],
        reviewer_ids=["security"],
        k=1,
    )


def _make_validated(
    finding: DeduplicatedFinding | None = None,
    status: ValidationStatus = ValidationStatus.UNVERIFIED,
    confidence: float = 8.0,
    notes: list[str] | None = None,
) -> ValidatedFinding:
    if finding is None:
        finding = _make_finding()
    return ValidatedFinding(
        finding=finding,
        validation_status=status,
        confidence=confidence,
        validation_notes=notes or [],
        weight=0.5,
    )




class TestStructuralVerification:
    """Layer 1: check file existence and line content."""

    def setup_method(self) -> None:
        self.validator = FindingValidator()

    def test_structural_nonexistent_file_returns_unverified(self) -> None:
        """Non-existent file -> UNVERIFIED, confidence halved."""
        finding = _make_finding(file="/nonexistent/path/does_not_exist.py", confidence=8.0)
        status, confidence, notes = self.validator.validate_structural(finding, file_content=None)
        assert status == ValidationStatus.UNVERIFIED
        assert confidence == pytest.approx(4.0)
        assert any("not found" in n.lower() or "does not exist" in n.lower() for n in notes)

    def test_structural_real_code_returns_verified(self, tmp_path: Path) -> None:
        """File with real code at reported line -> VERIFIED."""
        py_file = tmp_path / "app.py"
        py_file.write_text(
            "def foo():\n"
            "    x = 1\n"
            "    return x\n"
        )
        finding = _make_finding(file=str(py_file), line_start=2, line_end=2)
        status, confidence, notes = self.validator.validate_structural(
            finding, file_content=py_file.read_text()
        )
        assert status == ValidationStatus.VERIFIED

    def test_structural_comment_line_returns_unverified(self, tmp_path: Path) -> None:
        """Line that is a comment (starts with #) -> UNVERIFIED."""
        py_file = tmp_path / "app.py"
        py_file.write_text(
            "def foo():\n"
            "    # this is a comment\n"
            "    return 1\n"
        )
        finding = _make_finding(file=str(py_file), line_start=2, line_end=2, confidence=6.0)
        status, confidence, notes = self.validator.validate_structural(
            finding, file_content=py_file.read_text()
        )
        assert status == ValidationStatus.UNVERIFIED
        assert confidence == pytest.approx(3.0)

    def test_structural_non_python_unchanged(self, tmp_path: Path) -> None:
        """Non-.py files skip AST check and are treated as VERIFIED."""
        js_file = tmp_path / "app.js"
        js_file.write_text("const x = 1;\n")
        finding = _make_finding(file=str(js_file), line_start=1, line_end=1)
        status, confidence, notes = self.validator.validate_structural(
            finding, file_content=js_file.read_text()
        )
        assert status == ValidationStatus.VERIFIED

    def test_structural_empty_line_returns_unverified(self, tmp_path: Path) -> None:
        """Line that is whitespace-only -> UNVERIFIED."""
        py_file = tmp_path / "app.py"
        py_file.write_text("def foo():\n\n    return 1\n")
        finding = _make_finding(file=str(py_file), line_start=2, line_end=2, confidence=4.0)
        status, confidence, notes = self.validator.validate_structural(
            finding, file_content=py_file.read_text()
        )
        assert status == ValidationStatus.UNVERIFIED
        assert confidence == pytest.approx(2.0)

    def test_structural_line_out_of_range_returns_unverified(self, tmp_path: Path) -> None:
        """Line number beyond end of file -> UNVERIFIED."""
        py_file = tmp_path / "app.py"
        py_file.write_text("x = 1\n")
        finding = _make_finding(file=str(py_file), line_start=999, line_end=999, confidence=5.0)
        status, confidence, notes = self.validator.validate_structural(
            finding, file_content=py_file.read_text()
        )
        assert status == ValidationStatus.UNVERIFIED




class TestCrossCheckTaskSpec:
    """Layer 2: build_cross_check_task spec shape."""

    def setup_method(self) -> None:
        self.validator = FindingValidator()

    def test_cross_check_task_spec_uses_haiku(self) -> None:
        """Task spec must target a Haiku model (different from reviewer models)."""
        vf = _make_validated()
        code_snippet = "x = eval(user_input)  # line 10"
        spec = self.validator.build_cross_check_task(vf, code_snippet)

        assert "model" in spec
        assert "haiku" in spec["model"].lower()

    def test_cross_check_task_spec_contains_prompt(self) -> None:
        """Task spec must include a prompt field."""
        vf = _make_validated()
        spec = self.validator.build_cross_check_task(vf, "some code")
        assert "prompt" in spec
        assert isinstance(spec["prompt"], str)
        assert len(spec["prompt"]) > 0

    def test_cross_check_task_spec_prompt_includes_yes_no_instruction(self) -> None:
        """Prompt must instruct model to reply YES or NO on first line."""
        vf = _make_validated()
        spec = self.validator.build_cross_check_task(vf, "some code")
        prompt = spec["prompt"].lower()
        assert "yes" in prompt and "no" in prompt

    def test_cross_check_task_spec_includes_code_snippet(self) -> None:
        """Task spec prompt must contain the code snippet."""
        vf = _make_validated()
        code = "x = eval(user_input)"
        spec = self.validator.build_cross_check_task(vf, code)
        assert code in spec["prompt"]

    def test_cross_check_task_spec_includes_finding_description(self) -> None:
        """Task spec prompt must reference the finding description."""
        finding = _make_finding(description="Arbitrary code execution via eval")
        vf = _make_validated(finding=finding)
        spec = self.validator.build_cross_check_task(vf, "some code")
        assert "Arbitrary code execution via eval" in spec["prompt"]


class TestApplyCrossCheckResult:
    """Layer 2: apply_cross_check_result parses YES/NO and adjusts state."""

    def setup_method(self) -> None:
        self.validator = FindingValidator()

    def test_cross_check_no_marks_disputed(self) -> None:
        """Response starting with NO -> status=DISPUTED, confidence *= 0.3."""
        vf = _make_validated(confidence=8.0)
        result = self.validator.apply_cross_check_result(vf, "NO\nThis finding is not valid.")
        assert result.validation_status == ValidationStatus.DISPUTED
        assert result.confidence == pytest.approx(2.4)

    def test_cross_check_yes_unchanged(self) -> None:
        """Response starting with YES -> status and confidence unchanged."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=8.0)
        result = self.validator.apply_cross_check_result(vf, "YES\nThis finding is valid.")
        assert result.validation_status == ValidationStatus.VERIFIED
        assert result.confidence == pytest.approx(8.0)

    def test_cross_check_no_case_insensitive(self) -> None:
        """NO matching is case-insensitive."""
        vf = _make_validated(confidence=5.0)
        result = self.validator.apply_cross_check_result(vf, "no\nNot a real issue.")
        assert result.validation_status == ValidationStatus.DISPUTED
        assert result.confidence == pytest.approx(1.5)

    def test_cross_check_yes_case_insensitive(self) -> None:
        """YES matching is case-insensitive."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=7.0)
        result = self.validator.apply_cross_check_result(vf, "yes\nConfirmed.")
        assert result.validation_status == ValidationStatus.VERIFIED
        assert result.confidence == pytest.approx(7.0)

    def test_cross_check_ambiguous_response_unchanged(self) -> None:
        """Response that is neither YES nor NO -> no change."""
        vf = _make_validated(status=ValidationStatus.UNVERIFIED, confidence=6.0)
        result = self.validator.apply_cross_check_result(vf, "MAYBE this is an issue.")
        assert result.validation_status == ValidationStatus.UNVERIFIED
        assert result.confidence == pytest.approx(6.0)

    def test_cross_check_note_added_on_no(self) -> None:
        """Disputed cross-check adds an explanatory note."""
        vf = _make_validated()
        result = self.validator.apply_cross_check_result(vf, "NO\nFalse positive.")
        assert len(result.validation_notes) > 0




class TestHistoricalPatternMatch:
    """Layer 3: validate_historical queries retriever for past patterns."""

    def setup_method(self) -> None:
        self.validator = FindingValidator()

    def _mock_retriever(self, texts: list[str]) -> MagicMock:
        """Build a mock retriever that returns chunks with given texts."""
        retriever = MagicMock()
        results = []
        for text in texts:
            chunk = MagicMock()
            chunk.text = text
            tagged = MagicMock()
            tagged.chunk = chunk
            results.append(tagged)
        retriever.retrieve.return_value = results
        return retriever

    def test_historical_rejected_sets_status(self) -> None:
        """Retriever results containing 'rejected' -> HISTORICALLY_REJECTED."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=8.0)
        retriever = self._mock_retriever(["This pattern was rejected as a false positive"])
        result = self.validator.validate_historical(vf, retriever)
        assert result.validation_status == ValidationStatus.HISTORICALLY_REJECTED

    def test_historical_accepted_boosts_confidence(self) -> None:
        """Retriever results containing 'accepted' -> confidence *= 1.2 (max 10.0)."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=5.0)
        retriever = self._mock_retriever(["This pattern was accepted and confirmed as valid"])
        result = self.validator.validate_historical(vf, retriever)
        assert result.confidence == pytest.approx(6.0)

    def test_historical_accepted_confidence_capped_at_10(self) -> None:
        """Confidence boost does not exceed 10.0."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=9.5)
        retriever = self._mock_retriever(["accepted by team"])
        result = self.validator.validate_historical(vf, retriever)
        assert result.confidence <= 10.0
        assert result.confidence == pytest.approx(10.0)

    def test_historical_no_match_unchanged(self) -> None:
        """Empty retriever results -> no change to status or confidence."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=7.0)
        retriever = self._mock_retriever([])
        result = self.validator.validate_historical(vf, retriever)
        assert result.validation_status == ValidationStatus.VERIFIED
        assert result.confidence == pytest.approx(7.0)

    def test_historical_no_match_unrelated_text_unchanged(self) -> None:
        """Retriever results with unrelated text -> no change."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=7.0)
        retriever = self._mock_retriever(["SQL injection in user login form"])
        result = self.validator.validate_historical(vf, retriever)
        assert result.validation_status == ValidationStatus.VERIFIED
        assert result.confidence == pytest.approx(7.0)

    def test_historical_rejected_takes_priority_over_accepted(self) -> None:
        """If results contain both 'rejected' and 'accepted', rejected wins."""
        vf = _make_validated(status=ValidationStatus.VERIFIED, confidence=8.0)
        retriever = self._mock_retriever([
            "This was accepted in similar contexts",
            "This pattern was rejected as noise",
        ])
        result = self.validator.validate_historical(vf, retriever)
        assert result.validation_status == ValidationStatus.HISTORICALLY_REJECTED

    def test_historical_note_added_on_match(self) -> None:
        """Historical match adds a note to validation_notes."""
        vf = _make_validated()
        retriever = self._mock_retriever(["accepted pattern"])
        result = self.validator.validate_historical(vf, retriever)
        assert len(result.validation_notes) > 0




class TestFailOpen:
    """PROP-001: All exceptions must be swallowed; finding keeps current state."""

    def setup_method(self) -> None:
        self.validator = FindingValidator()

    def test_validate_never_raises_on_bad_file(self) -> None:
        """validate() with a non-existent file must not raise."""
        finding = _make_finding(file="/totally/nonexistent.py")
        result = self.validator.validate(finding)
        assert isinstance(result, ValidatedFinding)

    def test_validate_never_raises_when_retriever_explodes(self) -> None:
        """validate() must not raise even if retriever.retrieve() raises."""
        finding = _make_finding()
        retriever = MagicMock()
        retriever.retrieve.side_effect = RuntimeError("retriever is on fire")
        result = self.validator.validate(finding, retriever=retriever)
        assert isinstance(result, ValidatedFinding)

    def test_validate_never_raises_on_corrupted_file_content(self) -> None:
        """validate() must not raise with binary/garbage file_content."""
        finding = _make_finding()
        result = self.validator.validate(finding, file_content="\x00\x01\x02garbage")
        assert isinstance(result, ValidatedFinding)

    def test_validate_skip_cross_check_flag(self) -> None:
        """skip_cross_check=True skips Layer 2 entirely."""
        finding = _make_finding()
        result = self.validator.validate(finding, skip_cross_check=True)
        assert isinstance(result, ValidatedFinding)
        assert result.validation_status != ValidationStatus.DISPUTED

    def test_structural_exception_swallowed(self) -> None:
        """If validate_structural raises internally, validate() keeps going."""
        finding = _make_finding()
        original_validate_structural = self.validator.validate_structural

        def exploding_structural(f, fc):
            raise ValueError("structural exploded")

        self.validator.validate_structural = exploding_structural
        result = self.validator.validate(finding)
        assert isinstance(result, ValidatedFinding)




class TestWeightMapping:
    """ValidatedFinding.weight reflects ValidationStatus correctly."""

    def setup_method(self) -> None:
        self.validator = FindingValidator()

    def _result_with_status(self, status: ValidationStatus) -> ValidatedFinding:
        """Drive validator to produce a finding with the given status."""
        finding = _make_finding(file="/nonexistent/file.py")
        vf = _make_validated(finding=finding, status=status, confidence=5.0)
        return self.validator._apply_weight(vf)

    def test_weight_verified(self) -> None:
        vf = self._result_with_status(ValidationStatus.VERIFIED)
        assert vf.weight == pytest.approx(1.0)

    def test_weight_unverified(self) -> None:
        vf = self._result_with_status(ValidationStatus.UNVERIFIED)
        assert vf.weight == pytest.approx(0.5)

    def test_weight_disputed(self) -> None:
        vf = self._result_with_status(ValidationStatus.DISPUTED)
        assert vf.weight == pytest.approx(0.2)

    def test_weight_historically_rejected(self) -> None:
        vf = self._result_with_status(ValidationStatus.HISTORICALLY_REJECTED)
        assert vf.weight == pytest.approx(0.0)




class TestValidateIntegration:
    """End-to-end validate() flow with all layers."""

    def setup_method(self) -> None:
        self.validator = FindingValidator()

    def test_validate_returns_validated_finding(self) -> None:
        """validate() always returns a ValidatedFinding instance."""
        finding = _make_finding(file="/nonexistent.py")
        result = self.validator.validate(finding)
        assert isinstance(result, ValidatedFinding)

    def test_validate_with_real_file_and_no_retriever(self, tmp_path: Path) -> None:
        """Full flow: real file, no retriever, no cross-check (skip=True)."""
        py_file = tmp_path / "app.py"
        py_file.write_text("def foo():\n    x = eval(user_input)\n    return x\n")
        finding = _make_finding(file=str(py_file), line_start=2, line_end=2)
        result = self.validator.validate(
            finding,
            file_content=py_file.read_text(),
            skip_cross_check=True,
        )
        assert isinstance(result, ValidatedFinding)
        assert result.validation_status == ValidationStatus.VERIFIED

    def test_validate_historical_rejected_produces_zero_weight(self, tmp_path: Path) -> None:
        """HISTORICALLY_REJECTED findings get weight=0.0."""
        py_file = tmp_path / "app.py"
        py_file.write_text("x = eval(user_input)\n")
        finding = _make_finding(file=str(py_file), line_start=1, line_end=1)

        retriever = MagicMock()
        chunk = MagicMock()
        chunk.text = "historically rejected false positive"
        tagged = MagicMock()
        tagged.chunk = chunk
        retriever.retrieve.return_value = [tagged]

        result = self.validator.validate(
            finding,
            file_content=py_file.read_text(),
            retriever=retriever,
            skip_cross_check=True,
        )
        assert result.validation_status == ValidationStatus.HISTORICALLY_REJECTED
        assert result.weight == pytest.approx(0.0)

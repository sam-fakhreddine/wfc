"""Tests for the Consensus Score (CS) algorithm.

TDD tests for TASK-003: CS = (0.5 * R_bar) + (0.3 * R_bar * (k/n)) + (0.2 * R_max)
"""

from __future__ import annotations

import pytest

from wfc.scripts.skills.review.consensus_score import (
    ConsensusScore,
    ConsensusScoreResult,
    ScoredFinding,
)
from wfc.scripts.skills.review.fingerprint import DeduplicatedFinding


def _make_finding(
    severity: float = 5.0,
    confidence: float = 5.0,
    k: int = 1,
    category: str = "security",
    file: str = "app.py",
    line_start: int = 10,
) -> DeduplicatedFinding:
    """Helper to build a DeduplicatedFinding with sensible defaults."""
    return DeduplicatedFinding(
        fingerprint="abc123",
        file=file,
        line_start=line_start,
        line_end=line_start + 5,
        category=category,
        severity=severity,
        confidence=confidence,
        description="test finding",
        descriptions=["test finding"],
        remediation=["fix it"],
        reviewer_ids=[f"r{i}" for i in range(k)],
        k=k,
    )


class TestRiComputation:
    """Test R_i = (severity * confidence) / 10, clamped to [0, 10]."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_basic_ri(self) -> None:
        f = _make_finding(severity=8.0, confidence=7.0)
        assert self.cs._compute_R_i(f) == pytest.approx(5.6)

    def test_ri_max_values(self) -> None:
        f = _make_finding(severity=10.0, confidence=10.0)
        assert self.cs._compute_R_i(f) == pytest.approx(10.0)

    def test_ri_zero_severity(self) -> None:
        f = _make_finding(severity=0.0, confidence=8.0)
        assert self.cs._compute_R_i(f) == pytest.approx(0.0)

    def test_ri_zero_confidence(self) -> None:
        f = _make_finding(severity=9.0, confidence=0.0)
        assert self.cs._compute_R_i(f) == pytest.approx(0.0)

    def test_ri_clamped_upper(self) -> None:
        """Even though inputs shouldn't exceed 10, clamp ensures safety."""
        f = _make_finding(severity=12.0, confidence=10.0)
        assert self.cs._compute_R_i(f) == pytest.approx(10.0)

    def test_ri_clamped_lower(self) -> None:
        f = _make_finding(severity=-1.0, confidence=5.0)
        assert self.cs._compute_R_i(f) == pytest.approx(0.0)


class TestTierClassification:
    """Test CS -> tier mapping."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_informational_zero(self) -> None:
        assert self.cs._classify_tier(0.0) == "informational"

    def test_informational_boundary(self) -> None:
        assert self.cs._classify_tier(3.99) == "informational"

    def test_moderate_lower(self) -> None:
        assert self.cs._classify_tier(4.0) == "moderate"

    def test_moderate_upper(self) -> None:
        assert self.cs._classify_tier(6.99) == "moderate"

    def test_important_lower(self) -> None:
        assert self.cs._classify_tier(7.0) == "important"

    def test_important_upper(self) -> None:
        assert self.cs._classify_tier(8.99) == "important"

    def test_critical_lower(self) -> None:
        assert self.cs._classify_tier(9.0) == "critical"

    def test_critical_max(self) -> None:
        assert self.cs._classify_tier(10.0) == "critical"


class TestFindingTierClassification:
    """Test individual finding R_i -> tier mapping."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_informational(self) -> None:
        assert self.cs._classify_finding_tier(2.0) == "informational"

    def test_moderate(self) -> None:
        assert self.cs._classify_finding_tier(5.0) == "moderate"

    def test_important(self) -> None:
        assert self.cs._classify_finding_tier(7.5) == "important"

    def test_critical(self) -> None:
        assert self.cs._classify_finding_tier(9.5) == "critical"


class TestCSFormula:
    """Test the full CS formula: (0.5*R_bar) + (0.3*R_bar*(k/n)) + (0.2*R_max)."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_no_findings(self) -> None:
        result = self.cs.calculate([])
        assert result.cs == pytest.approx(0.0)
        assert result.tier == "informational"
        assert result.passed is True
        assert result.R_bar == pytest.approx(0.0)
        assert result.R_max == pytest.approx(0.0)
        assert result.k_total == 0
        assert result.n == 5
        assert result.findings == []

    def test_single_finding_scenario(self) -> None:
        """Test Scenario 1 from the task spec.

        Finding: severity=9.0, confidence=8.0, k=2
        R_i = 7.2
        R_bar = 7.2, k=2, n=5, R_max = 7.2
        CS = (0.5*7.2) + (0.3*7.2*(2/5)) + (0.2*7.2)
           = 3.6 + 0.864 + 1.44 = 5.904
        Tier: Moderate
        """
        findings = [_make_finding(severity=9.0, confidence=8.0, k=2)]
        result = self.cs.calculate(findings)
        assert result.cs == pytest.approx(5.904, abs=1e-6)
        assert result.tier == "moderate"
        assert result.passed is True
        assert result.R_bar == pytest.approx(7.2)
        assert result.R_max == pytest.approx(7.2)
        assert result.k_total == 2

    def test_multiple_findings_scenario(self) -> None:
        """Test Scenario 2 from the task spec.

        Finding A: severity=9.5, confidence=9.0, k=3 -> R_A = 8.55
        Finding B: severity=6.0, confidence=7.0, k=2 -> R_B = 4.2
        R_bar = (8.55 + 4.2) / 2 = 6.375
        k = 3+2 = 5, n = 5, R_max = 8.55
        CS = (0.5*6.375) + (0.3*6.375*(5/5)) + (0.2*8.55)
           = 3.1875 + 1.9125 + 1.71 = 6.81
        Tier: Moderate
        """
        findings = [
            _make_finding(severity=9.5, confidence=9.0, k=3),
            _make_finding(severity=6.0, confidence=7.0, k=2),
        ]
        result = self.cs.calculate(findings)
        assert result.cs == pytest.approx(6.81, abs=1e-6)
        assert result.tier == "moderate"
        assert result.passed is True
        assert result.R_bar == pytest.approx(6.375)
        assert result.R_max == pytest.approx(8.55)
        assert result.k_total == 5

    def test_no_agreement_vs_full_agreement(self) -> None:
        """k=1 (no extra agreement) vs k=5 (all agree) changes the agreement term."""
        finding_no_agree = [_make_finding(severity=8.0, confidence=8.0, k=1)]
        finding_full_agree = [_make_finding(severity=8.0, confidence=8.0, k=5)]

        result_no = self.cs.calculate(finding_no_agree)
        result_full = self.cs.calculate(finding_full_agree)

        assert result_no.cs == pytest.approx(4.864, abs=1e-6)
        assert result_full.cs == pytest.approx(6.4, abs=1e-6)
        assert result_full.cs > result_no.cs


class TestPassedLogic:
    """Test that passed reflects the tier correctly."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_informational_passes(self) -> None:
        findings = [_make_finding(severity=2.0, confidence=2.0, k=1)]
        result = self.cs.calculate(findings)
        assert result.tier == "informational"
        assert result.passed is True

    def test_moderate_passes(self) -> None:
        findings = [_make_finding(severity=9.0, confidence=8.0, k=2)]
        result = self.cs.calculate(findings)
        assert result.tier == "moderate"
        assert result.passed is True

    def test_important_fails(self) -> None:
        findings = [
            _make_finding(severity=10.0, confidence=10.0, k=4),
            _make_finding(severity=9.0, confidence=9.0, k=4),
        ]
        result = self.cs.calculate(findings)
        assert result.tier in ("important", "critical")
        assert result.passed is False

    def test_critical_fails(self) -> None:
        findings = [
            _make_finding(severity=10.0, confidence=10.0, k=5),
            _make_finding(severity=10.0, confidence=10.0, k=5),
            _make_finding(severity=10.0, confidence=10.0, k=5),
        ]
        result = self.cs.calculate(findings)
        assert result.tier == "critical"
        assert result.passed is False


class TestEdgeCases:
    """Test edge cases."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_all_zero_severity(self) -> None:
        findings = [
            _make_finding(severity=0.0, confidence=5.0, k=1),
            _make_finding(severity=0.0, confidence=8.0, k=3),
        ]
        result = self.cs.calculate(findings)
        assert result.cs == pytest.approx(0.0)
        assert result.tier == "informational"

    def test_single_max_finding(self) -> None:
        """Single finding with max values: sev=10, conf=10, k=5.

        R_i = 10.0
        R_bar = 10.0, k=5, n=5, R_max=10.0
        CS = (0.5*10) + (0.3*10*(5/5)) + (0.2*10) = 5 + 3 + 2 = 10.0
        """
        findings = [_make_finding(severity=10.0, confidence=10.0, k=5)]
        result = self.cs.calculate(findings)
        assert result.cs == pytest.approx(10.0)
        assert result.tier == "critical"
        assert result.passed is False

    def test_many_findings(self) -> None:
        """20+ findings should still work correctly."""
        findings = [_make_finding(severity=3.0, confidence=3.0, k=1) for _ in range(25)]
        result = self.cs.calculate(findings)
        assert len(result.findings) == 25
        assert result.cs == pytest.approx(1.98, abs=1e-6)

    def test_minority_protection_not_applied_by_default(self) -> None:
        """Non-protected domain findings don't trigger MPR."""
        findings = [_make_finding(severity=5.0, confidence=5.0, k=1)]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is False


class TestSummaryGeneration:
    """Test that summary includes useful information."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_summary_includes_tier(self) -> None:
        findings = [_make_finding(severity=9.0, confidence=8.0, k=2)]
        result = self.cs.calculate(findings)
        assert result.tier in result.summary.lower()

    def test_summary_includes_finding_count(self) -> None:
        findings = [
            _make_finding(severity=5.0, confidence=5.0, k=1),
            _make_finding(severity=3.0, confidence=3.0, k=1),
        ]
        result = self.cs.calculate(findings)
        assert "2" in result.summary

    def test_summary_no_findings(self) -> None:
        result = self.cs.calculate([])
        assert "0" in result.summary or "no" in result.summary.lower()


class TestConsensusScoreResult:
    """Test the result dataclass structure."""

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_result_fields(self) -> None:
        findings = [_make_finding(severity=7.0, confidence=6.0, k=2)]
        result = self.cs.calculate(findings)

        assert isinstance(result, ConsensusScoreResult)
        assert isinstance(result.cs, float)
        assert isinstance(result.tier, str)
        assert isinstance(result.findings, list)
        assert isinstance(result.findings[0], ScoredFinding)
        assert isinstance(result.R_bar, float)
        assert isinstance(result.R_max, float)
        assert isinstance(result.k_total, int)
        assert result.n == 5
        assert isinstance(result.passed, bool)
        assert isinstance(result.minority_protection_applied, bool)
        assert isinstance(result.summary, str)

    def test_scored_finding_fields(self) -> None:
        findings = [_make_finding(severity=7.0, confidence=6.0, k=2)]
        result = self.cs.calculate(findings)
        sf = result.findings[0]

        assert sf.finding is findings[0]
        assert sf.R_i == pytest.approx(4.2)
        assert sf.tier == "moderate"


def _make_finding_with_reviewers(
    severity: float = 5.0,
    confidence: float = 5.0,
    k: int = 1,
    reviewer_ids: list[str] | None = None,
    category: str = "security",
    file: str = "app.py",
    line_start: int = 10,
) -> DeduplicatedFinding:
    """Helper to build a DeduplicatedFinding with explicit reviewer_ids."""
    if reviewer_ids is None:
        reviewer_ids = ["security"]
    return DeduplicatedFinding(
        fingerprint="abc123",
        file=file,
        line_start=line_start,
        line_end=line_start + 5,
        category=category,
        severity=severity,
        confidence=confidence,
        description="test finding",
        descriptions=["test finding"],
        remediation=["fix it"],
        reviewer_ids=reviewer_ids,
        k=k,
    )


class TestMinorityProtection:
    """Test Minority Protection Rule (MPR): Black Swan Detection.

    MPR: IF R_max >= 8.5 AND k >= 1 AND finding from security/reliability THEN
         CS_final = max(CS, 0.7 * R_max + 2.0)
    """

    def setup_method(self) -> None:
        self.cs = ConsensusScore()

    def test_security_finding_triggers_mpr(self) -> None:
        """Security finding with R_max=9.5, k=1 -> MPR triggers, CS elevated.

        R_i = (9.5 * 10.0) / 10 = 9.5, k=1
        Normal CS = (0.5*9.5) + (0.3*9.5*(1/5)) + (0.2*9.5) = 4.75 + 0.57 + 1.9 = 7.22
        MPR: R_max=9.5 >= 8.5, k=1 >= 1, reviewer=security -> applies
        CS_final = max(7.22, 0.7*9.5 + 2.0) = max(7.22, 8.65) = 8.65
        """
        findings = [_make_finding_with_reviewers(
            severity=9.5, confidence=10.0, k=1, reviewer_ids=["security"],
        )]
        result = self.cs.calculate(findings)
        assert result.cs == pytest.approx(8.65, abs=1e-6)
        assert result.minority_protection_applied is True

    def test_reliability_finding_triggers_mpr_boundary(self) -> None:
        """Reliability finding with R_max=8.5, k=1 -> MPR triggers (boundary).

        R_i = (8.5 * 10.0) / 10 = 8.5, k=1
        Normal CS = (0.5*8.5) + (0.3*8.5*(1/5)) + (0.2*8.5) = 4.25 + 0.51 + 1.7 = 6.46
        MPR: R_max=8.5 >= 8.5, k=1 >= 1, reviewer=reliability -> applies
        CS_final = max(6.46, 0.7*8.5 + 2.0) = max(6.46, 7.95) = 7.95
        """
        findings = [_make_finding_with_reviewers(
            severity=8.5, confidence=10.0, k=1, reviewer_ids=["reliability"],
        )]
        result = self.cs.calculate(findings)
        assert result.cs == pytest.approx(7.95, abs=1e-6)
        assert result.minority_protection_applied is True

    def test_performance_finding_does_not_trigger_mpr(self) -> None:
        """Performance finding with R_max=9.5, k=1 -> MPR does NOT trigger."""
        findings = [_make_finding_with_reviewers(
            severity=9.5, confidence=10.0, k=1, reviewer_ids=["performance"],
        )]
        result = self.cs.calculate(findings)
        expected_cs = (0.5 * 9.5) + (0.3 * 9.5 * (1 / 5)) + (0.2 * 9.5)
        assert result.cs == pytest.approx(expected_cs, abs=1e-6)
        assert result.minority_protection_applied is False

    def test_correctness_finding_does_not_trigger_mpr(self) -> None:
        """Correctness finding with R_max=9.0, k=1 -> MPR does NOT trigger."""
        findings = [_make_finding_with_reviewers(
            severity=9.0, confidence=10.0, k=1, reviewer_ids=["correctness"],
        )]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is False

    def test_maintainability_finding_does_not_trigger_mpr(self) -> None:
        """Maintainability finding with R_max=9.0, k=1 -> MPR does NOT trigger."""
        findings = [_make_finding_with_reviewers(
            severity=9.0, confidence=10.0, k=1, reviewer_ids=["maintainability"],
        )]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is False

    def test_below_threshold_does_not_trigger_mpr(self) -> None:
        """R_max=8.4 from Security -> MPR does NOT trigger (below threshold)."""
        findings = [_make_finding_with_reviewers(
            severity=8.4, confidence=10.0, k=1, reviewer_ids=["security"],
        )]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is False

    def test_mpr_sets_flag_true(self) -> None:
        """MPR applied -> minority_protection_applied=True in result."""
        findings = [_make_finding_with_reviewers(
            severity=9.0, confidence=10.0, k=1, reviewer_ids=["security"],
        )]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is True

    def test_mpr_changes_tier(self) -> None:
        """MPR can change tier from moderate to important.

        Construct a scenario where normal CS is moderate but MPR elevates to important.
        Security finding: severity=9.5, confidence=10.0, k=1 -> R_i=9.5
        Normal CS = 7.22 (important already). Let's use a scenario with lower normal CS.

        Use severity=8.5, confidence=10.0 -> R_i=8.5, k=1
        Normal CS = (0.5*8.5) + (0.3*8.5*0.2) + (0.2*8.5) = 4.25 + 0.51 + 1.7 = 6.46 (moderate)
        MPR: max(6.46, 0.7*8.5+2.0) = max(6.46, 7.95) = 7.95 (important)
        """
        findings = [_make_finding_with_reviewers(
            severity=8.5, confidence=10.0, k=1, reviewer_ids=["security"],
        )]
        result = self.cs.calculate(findings)
        assert result.tier == "important"
        assert result.passed is False

    def test_mpr_not_applied_preserves_false(self) -> None:
        """MPR not applied -> minority_protection_applied=False (existing behavior)."""
        findings = [_make_finding_with_reviewers(
            severity=5.0, confidence=5.0, k=1, reviewer_ids=["performance"],
        )]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is False

    def test_security_and_reliability_both_flag(self) -> None:
        """Security + Reliability both flag same issue -> MPR triggers.

        reviewer_ids=["security", "reliability"], k=2
        severity=9.0, confidence=10.0 -> R_i=9.0
        Normal CS = (0.5*9.0) + (0.3*9.0*(2/5)) + (0.2*9.0) = 4.5 + 1.08 + 1.8 = 7.38
        MPR: R_max=9.0 >= 8.5, from security+reliability -> applies
        CS_final = max(7.38, 0.7*9.0 + 2.0) = max(7.38, 8.3) = 8.3
        """
        findings = [_make_finding_with_reviewers(
            severity=9.0, confidence=10.0, k=2, reviewer_ids=["security", "reliability"],
        )]
        result = self.cs.calculate(findings)
        assert result.cs == pytest.approx(8.3, abs=1e-6)
        assert result.minority_protection_applied is True

    def test_summary_mentions_minority_protection(self) -> None:
        """Summary mentions minority protection when MPR is applied."""
        findings = [_make_finding_with_reviewers(
            severity=9.5, confidence=10.0, k=1, reviewer_ids=["security"],
        )]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is True
        assert "minority protection" in result.summary.lower()

    def test_mpr_uses_max_ri_finding_reviewers(self) -> None:
        """MPR checks reviewer_ids of the finding that produced R_max.

        Finding A: severity=5.0, conf=5.0, k=1, reviewer=security -> R_i=2.5
        Finding B: severity=9.5, conf=10.0, k=1, reviewer=performance -> R_i=9.5 (R_max)
        R_max finding is from performance, NOT security -> MPR does NOT trigger.
        """
        findings = [
            _make_finding_with_reviewers(
                severity=5.0, confidence=5.0, k=1, reviewer_ids=["security"],
                line_start=10,
            ),
            _make_finding_with_reviewers(
                severity=9.5, confidence=10.0, k=1, reviewer_ids=["performance"],
                line_start=50,
            ),
        ]
        result = self.cs.calculate(findings)
        assert result.minority_protection_applied is False

"""Consensus Score (CS) algorithm for the 5-agent review system.

CS = (0.5 * R_bar) + (0.3 * R_bar * (k/n)) + (0.2 * R_max)

Where:
- R_i = (S_i * C_i) / 10 for each deduplicated finding
- R_bar = mean of all R_i
- k = total reviewer agreements (sum of DeduplicatedFinding.k)
- n = 5 (total reviewers)
- R_max = max(R_i) across all findings

Decision tiers:
- Informational: CS < 4.0  (log only)
- Moderate:      4.0 <= CS < 7.0  (inline comment)
- Important:     7.0 <= CS < 9.0  (block merge)
- Critical:      CS >= 9.0  (block + escalate)
"""

from __future__ import annotations

from dataclasses import dataclass

from wfc.scripts.orchestrators.review.fingerprint import DeduplicatedFinding


@dataclass
class ScoredFinding:
    """A finding with its computed relevance score R_i."""

    finding: DeduplicatedFinding
    R_i: float
    tier: str


@dataclass
class ConsensusScoreResult:
    """Result of the Consensus Score calculation."""

    cs: float
    tier: str
    findings: list[ScoredFinding]
    R_bar: float
    R_max: float
    k_total: int
    n: int
    passed: bool
    minority_protection_applied: bool
    summary: str


class ConsensusScore:
    """Consensus Score algorithm for the 5-agent review system."""

    N_REVIEWERS: int = 5
    PROTECTION_DOMAINS: set[str] = {"security", "reliability"}

    def calculate(
        self,
        findings: list[DeduplicatedFinding],
        weights: dict[str, float] | None = None,
    ) -> ConsensusScoreResult:
        """Calculate the Consensus Score from deduplicated findings."""
        if not findings:
            return ConsensusScoreResult(
                cs=0.0,
                tier="informational",
                findings=[],
                R_bar=0.0,
                R_max=0.0,
                k_total=0,
                n=self.N_REVIEWERS,
                passed=True,
                minority_protection_applied=False,
                summary=self._generate_summary(0.0, "informational", [], False),
            )

        effective_weights: dict[str, float] = weights or {}
        active_findings = [f for f in findings if effective_weights.get(f.fingerprint, 1.0) > 0.0]

        if not active_findings:
            return ConsensusScoreResult(
                cs=0.0,
                tier="informational",
                findings=[],
                R_bar=0.0,
                R_max=0.0,
                k_total=0,
                n=self.N_REVIEWERS,
                passed=True,
                minority_protection_applied=False,
                summary=self._generate_summary(0.0, "informational", [], False),
            )

        scored = []
        for f in active_findings:
            weight = effective_weights.get(f.fingerprint, 1.0)
            r_i = self._compute_R_i(f) * weight
            scored.append(ScoredFinding(finding=f, R_i=r_i, tier=self._classify_finding_tier(r_i)))

        r_values = [sf.R_i for sf in scored]
        r_bar = sum(r_values) / len(r_values)
        r_max = max(r_values)
        k_total = sum(f.k for f in active_findings)

        cs = (0.5 * r_bar) + (0.3 * r_bar * (k_total / self.N_REVIEWERS)) + (0.2 * r_max)
        cs, mpr_applied = self._apply_minority_protection(cs, scored)
        tier = self._classify_tier(cs)
        passed = tier in ("informational", "moderate")

        return ConsensusScoreResult(
            cs=cs,
            tier=tier,
            findings=scored,
            R_bar=r_bar,
            R_max=r_max,
            k_total=k_total,
            n=self.N_REVIEWERS,
            passed=passed,
            minority_protection_applied=mpr_applied,
            summary=self._generate_summary(cs, tier, scored, mpr_applied),
        )

    def _apply_minority_protection(
        self,
        cs: float,
        scored: list[ScoredFinding],
    ) -> tuple[float, bool]:
        """Apply Minority Protection Rule (Black Swan Detection).

        IF R_max >= 8.5 AND k >= 1 AND R_max finding is from a protected domain:
            CS_final = max(CS, 0.7 * R_max + 2.0)
        """
        if not scored:
            return cs, False
        max_sf = max(scored, key=lambda sf: sf.R_i)
        r_max = max_sf.R_i
        if r_max < 8.5 or max_sf.finding.k < 1:
            return cs, False
        if not self.PROTECTION_DOMAINS.intersection(max_sf.finding.reviewer_ids):
            return cs, False
        elevated = 0.7 * r_max + 2.0
        if elevated > cs:
            return elevated, True
        return cs, True

    def _compute_R_i(self, finding: DeduplicatedFinding) -> float:
        """Compute R_i = (severity * confidence) / 10, clamped to [0, 10]."""
        raw = (finding.severity * finding.confidence) / 10.0
        return max(0.0, min(10.0, raw))

    def _classify_tier(self, cs: float) -> str:
        """Classify CS into a decision tier."""
        if cs < 4.0:
            return "informational"
        if cs < 7.0:
            return "moderate"
        if cs < 9.0:
            return "important"
        return "critical"

    def _classify_finding_tier(self, r_i: float) -> str:
        """Classify individual finding's R_i into a tier."""
        if r_i < 4.0:
            return "informational"
        if r_i < 7.0:
            return "moderate"
        if r_i < 9.0:
            return "important"
        return "critical"

    def _generate_summary(
        self,
        cs: float,
        tier: str,
        findings: list[ScoredFinding],
        mpr_applied: bool,
    ) -> str:
        """Generate human-readable summary."""
        count = len(findings)
        if count == 0:
            return f"CS={cs:.2f} ({tier}): 0 findings, review passed."

        passed = tier in ("informational", "moderate")
        status = "review passed" if passed else "review FAILED"
        base = f"CS={cs:.2f} ({tier}): {count} finding(s), {status}."
        if mpr_applied:
            base += " Minority protection applied."
        return base

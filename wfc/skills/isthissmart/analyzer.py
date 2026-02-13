"""
IsThisSmart Analyzer

7-dimension analysis of plans, ideas, and approaches.
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


class Verdict(Enum):
    """Analysis verdicts"""

    PROCEED = "🟢 PROCEED"
    PROCEED_WITH_ADJUSTMENTS = "🟡 PROCEED WITH ADJUSTMENTS"
    RECONSIDER = "🟠 RECONSIDER APPROACH"
    DONT_PROCEED = "🔴 DON'T PROCEED"


@dataclass
class DimensionAnalysis:
    """Analysis of a single dimension"""

    dimension: str
    score: int  # 1-10
    strengths: List[str]
    concerns: List[str]
    recommendation: str


@dataclass
class SmartAnalysis:
    """Complete IsThisSmart analysis"""

    subject: str
    verdict: Verdict
    overall_score: float
    dimensions: List[DimensionAnalysis]
    executive_summary: str
    alternatives: List[str]
    final_recommendation: str


class IsThisSmartAnalyzer:
    """
    Analyzes plans/ideas across 7 dimensions.

    Discerning but constructive. Honest but not harsh.
    """

    def analyze(self, subject: str, content: str) -> SmartAnalysis:
        """
        Perform 7-dimension analysis.

        Returns SmartAnalysis with verdict.
        """

        dimensions = [
            self._analyze_need(subject, content),
            self._analyze_simplicity(subject, content),
            self._analyze_scope(subject, content),
            self._analyze_tradeoffs(subject, content),
            self._analyze_risks(subject, content),
            self._analyze_blast_radius(subject, content),
            self._analyze_timeline(subject, content),
        ]

        # Calculate overall score
        overall_score = sum(d.score for d in dimensions) / len(dimensions)

        # Determine verdict
        verdict = self._determine_verdict(overall_score, dimensions)

        # Generate summary
        executive_summary = self._generate_summary(subject, dimensions, overall_score)

        # Suggest alternatives
        alternatives = self._suggest_alternatives(subject, content, dimensions)

        # Final recommendation
        final_recommendation = self._generate_recommendation(verdict, dimensions)

        return SmartAnalysis(
            subject=subject,
            verdict=verdict,
            overall_score=overall_score,
            dimensions=dimensions,
            executive_summary=executive_summary,
            alternatives=alternatives,
            final_recommendation=final_recommendation,
        )

    def _analyze_need(self, subject: str, content: str) -> DimensionAnalysis:
        """Dimension 1: Do we even need this?"""
        # Simplified - real implementation would use LLM
        return DimensionAnalysis(
            dimension="Do We Even Need This?",
            score=8,
            strengths=["Addresses clear user need", "Backed by data/metrics"],
            concerns=["Consider if existing solution could be improved instead"],
            recommendation="Need is justified, but validate assumptions",
        )

    def _analyze_simplicity(self, subject: str, content: str) -> DimensionAnalysis:
        """Dimension 2: Is this the simplest approach?"""
        return DimensionAnalysis(
            dimension="Is This the Simplest Approach?",
            score=7,
            strengths=["Architecture is clean", "Follows ELEGANT principles"],
            concerns=["Could start simpler and iterate", "Consider using existing library"],
            recommendation="Approach is reasonable, but explore simpler alternatives",
        )

    def _analyze_scope(self, subject: str, content: str) -> DimensionAnalysis:
        """Dimension 3: Is the scope right?"""
        return DimensionAnalysis(
            dimension="Is the Scope Right?",
            score=8,
            strengths=["Well-scoped for initial version", "Clear boundaries"],
            concerns=["Watch for scope creep during implementation"],
            recommendation="Scope is appropriate",
        )

    def _analyze_tradeoffs(self, subject: str, content: str) -> DimensionAnalysis:
        """Dimension 4: What are we trading off?"""
        return DimensionAnalysis(
            dimension="What Are We Trading Off?",
            score=7,
            strengths=["Tradeoffs acknowledged", "Maintenance burden considered"],
            concerns=["Opportunity cost of other features", "Long-term maintenance"],
            recommendation="Tradeoffs are acceptable but keep monitoring",
        )

    def _analyze_risks(self, subject: str, content: str) -> DimensionAnalysis:
        """Dimension 5: Have we seen this fail before?"""
        return DimensionAnalysis(
            dimension="Have We Seen This Fail Before?",
            score=8,
            strengths=["No obvious anti-patterns", "Follows best practices"],
            concerns=["Monitor for common pitfalls in similar systems"],
            recommendation="Risk level is acceptable",
        )

    def _analyze_blast_radius(self, subject: str, content: str) -> DimensionAnalysis:
        """Dimension 6: What's the blast radius?"""
        return DimensionAnalysis(
            dimension="What's the Blast Radius?",
            score=9,
            strengths=["Changes are isolated", "Easy rollback", "Good observability"],
            concerns=["Ensure monitoring is in place before launch"],
            recommendation="Blast radius is well-contained",
        )

    def _analyze_timeline(self, subject: str, content: str) -> DimensionAnalysis:
        """Dimension 7: Is the timeline realistic?"""
        return DimensionAnalysis(
            dimension="Is the Timeline Realistic?",
            score=7,
            strengths=["Phased approach", "Realistic complexity estimates"],
            concerns=["Integration risks may extend timeline", "Consider prototyping first"],
            recommendation="Timeline is reasonable with buffer",
        )

    def _determine_verdict(
        self, overall_score: float, dimensions: List[DimensionAnalysis]
    ) -> Verdict:
        """Determine overall verdict"""
        # Check for critical concerns
        has_low_score = any(d.score <= 4 for d in dimensions)

        if has_low_score:
            return Verdict.DONT_PROCEED
        elif overall_score >= 8.5:
            return Verdict.PROCEED
        elif overall_score >= 7.0:
            return Verdict.PROCEED_WITH_ADJUSTMENTS
        else:
            return Verdict.RECONSIDER

    def _generate_summary(
        self, subject: str, dimensions: List[DimensionAnalysis], score: float
    ) -> str:
        """Generate executive summary"""
        strengths_count = sum(len(d.strengths) for d in dimensions)
        concerns_count = sum(len(d.concerns) for d in dimensions)

        return f"""
Overall, this approach shows {strengths_count} clear strengths and {concerns_count} areas for consideration.

The strongest aspects are: {', '.join(d.dimension for d in sorted(dimensions, key=lambda x: x.score, reverse=True)[:3])}.

Key considerations: {', '.join(d.concerns[0] if d.concerns else 'None' for d in dimensions[:3])}.

With an overall score of {score:.1f}/10, this is a solid approach that can move forward with attention to the identified concerns.
        """.strip()

    def _suggest_alternatives(
        self, subject: str, content: str, dimensions: List[DimensionAnalysis]
    ) -> List[str]:
        """Suggest simpler alternatives"""
        # Simplified - real implementation would be smarter
        return [
            "Start with a simpler MVP and iterate based on feedback",
            "Consider using existing solution (e.g., off-the-shelf library) and extending it",
            "Phase the implementation - deliver core value first, add features later",
        ]

    def _generate_recommendation(
        self, verdict: Verdict, dimensions: List[DimensionAnalysis]
    ) -> str:
        """Generate final recommendation"""
        if verdict == Verdict.PROCEED:
            return "This is a smart approach. Proceed with confidence, keeping the identified concerns in mind."
        elif verdict == Verdict.PROCEED_WITH_ADJUSTMENTS:
            concerns = [c for d in dimensions for c in d.concerns]
            return f"Proceed, but address these key concerns first: {'; '.join(concerns[:3])}"
        elif verdict == Verdict.RECONSIDER:
            return "Consider the simpler alternatives suggested above before proceeding."
        else:
            low_dims = [d.dimension for d in dimensions if d.score <= 4]
            return f"Recommend not proceeding. Critical concerns in: {', '.join(low_dims)}"

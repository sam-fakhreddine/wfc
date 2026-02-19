"""
WFC Build - Complexity Assessor

SOLID: Single Responsibility - Only assesses complexity from interview results
"""

from dataclasses import dataclass
from typing import Tuple
from .interview import InterviewResult


@dataclass
class ComplexityRating:
    """Complexity assessment output"""
    rating: str  # "S", "M", "L", "XL"
    agent_count: int  # 1-5
    rationale: str
    recommendation: str = ""  # If XL, recommends wfc-plan


class ComplexityAssessor:
    """
    Analyzes interview responses and assigns complexity rating.

    PROPERTY: PROP-006 - Deterministic assessment (same input = same output)
    """

    # Complexity thresholds
    S_MAX_FILES = 1
    S_MAX_LOC = 50

    M_MAX_FILES = 3
    M_MAX_LOC = 200

    L_MAX_FILES = 10
    L_MAX_LOC = 500

    def assess(self, interview: InterviewResult) -> ComplexityRating:
        """
        Assess complexity from interview results.

        Args:
            interview: InterviewResult from quick interview

        Returns:
            ComplexityRating with rating, agent_count, rationale

        INVARIANT: Same interview → same rating (deterministic)
        """
        file_count = len(interview.files_affected)
        loc = interview.loc_estimate
        has_new_deps = len(interview.new_dependencies) > 0
        is_new_module = interview.scope == "new_module"

        # S: Single file, <50 LOC, no new deps, no arch impact
        if file_count <= self.S_MAX_FILES and loc <= self.S_MAX_LOC and not has_new_deps:
            return ComplexityRating(
                rating="S",
                agent_count=1,
                rationale=f"Simple change: {file_count} file(s), ~{loc} LOC, no new dependencies"
            )

        # M: 2-3 files, 50-200 LOC, minor deps, localized impact
        if file_count <= self.M_MAX_FILES and loc <= self.M_MAX_LOC:
            agent_count = 1 if file_count <= 2 and loc < 100 else 2
            return ComplexityRating(
                rating="M",
                agent_count=agent_count,
                rationale=f"Medium change: {file_count} file(s), ~{loc} LOC, localized impact"
            )

        # L: 4-10 files, 200-500 LOC, new module, moderate impact
        if file_count <= self.L_MAX_FILES and loc <= self.L_MAX_LOC:
            agent_count = 2 if file_count <= 6 else 3
            return ComplexityRating(
                rating="L",
                agent_count=agent_count,
                rationale=f"Large change: {file_count} file(s), ~{loc} LOC" +
                         (", new module" if is_new_module else "")
            )

        # XL: >10 files, >500 LOC, major refactor → recommend wfc-plan
        return ComplexityRating(
            rating="XL",
            agent_count=5,
            rationale=f"Extra large change: {file_count} file(s), ~{loc} LOC - too complex for quick build",
            recommendation="This complexity requires formal planning. Use /wfc-plan + /wfc-implement instead."
        )

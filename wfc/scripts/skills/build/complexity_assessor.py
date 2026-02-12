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
        # TODO: Implement complexity assessment logic
        # This is a placeholder that will be implemented in TASK-003
        raise NotImplementedError("Complexity assessment not yet implemented")

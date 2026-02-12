"""
WFC Build - Quick Interview

SOLID: Single Responsibility - Only handles interview logic
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InterviewResult:
    """Structured interview output"""
    feature_description: str
    scope: str  # "single_file", "few_files", "many_files", "new_module"
    files_affected: List[str]
    loc_estimate: int
    new_dependencies: List[str]
    constraints: List[str]
    test_context: Optional[str] = None


class QuickInterview:
    """
    Conducts streamlined 3-5 question interview.

    PROPERTY: PROP-008 - Must complete in <30 seconds
    """

    def __init__(self):
        self.max_questions = 5

    def conduct(self, feature_hint: Optional[str] = None) -> InterviewResult:
        """
        Conduct quick adaptive interview.

        Args:
            feature_hint: Optional pre-provided feature description

        Returns:
            InterviewResult with structured responses
        """
        # TODO: Implement interview logic
        # This is a placeholder that will be implemented in TASK-002
        raise NotImplementedError("Interview logic not yet implemented")

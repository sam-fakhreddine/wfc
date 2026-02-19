"""
WFC Build - Quick Interview

SOLID: Single Responsibility - Only handles interview logic
"""

from dataclasses import dataclass
from typing import List, Optional
import re


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
        # Q1: Feature description (skip if hint provided)
        if feature_hint:
            feature_description = feature_hint
        else:
            feature_description = self._ask_feature_description()

        # Q2: Scope
        scope = self._ask_scope()

        # Q3: Adaptive - depends on scope
        if scope == "single_file":
            files_affected = self._ask_which_file()
            loc_estimate = self._estimate_loc_simple()
        elif scope == "few_files":
            files_affected = self._ask_which_files()
            loc_estimate = self._estimate_loc_medium()
        elif scope == "many_files":
            files_affected = self._ask_architecture_pattern()
            loc_estimate = self._estimate_loc_large()
        else:  # new_module
            files_affected = self._ask_module_structure()
            loc_estimate = self._estimate_loc_module()

        # Q4: Constraints
        constraints = self._ask_constraints()

        # Q5: Dependencies (derived from constraints + scope)
        new_dependencies = self._ask_dependencies(scope, constraints)

        # Q6 (optional): Test context
        test_context = self._ask_test_context() if scope != "single_file" else None

        return InterviewResult(
            feature_description=feature_description,
            scope=scope,
            files_affected=files_affected,
            loc_estimate=loc_estimate,
            new_dependencies=new_dependencies,
            constraints=constraints,
            test_context=test_context
        )

    def _ask_feature_description(self) -> str:
        """Q1: What feature do you want to build?"""
        # This would use AskUserQuestion in real implementation
        # For now, return placeholder
        return "Feature description (interview placeholder)"

    def _ask_scope(self) -> str:
        """Q2: What's the scope?"""
        # Options: single_file, few_files, many_files, new_module
        return "single_file"

    def _ask_which_file(self) -> List[str]:
        """Q3a: Which file?"""
        return ["example.py"]

    def _ask_which_files(self) -> List[str]:
        """Q3b: Which files?"""
        return ["file1.py", "file2.py"]

    def _ask_architecture_pattern(self) -> List[str]:
        """Q3c: What architectural pattern?"""
        # User describes pattern, we infer files
        return [f"file{i}.py" for i in range(5)]

    def _ask_module_structure(self) -> List[str]:
        """Q3d: Module structure?"""
        return ["module/__init__.py", "module/core.py"]

    def _ask_constraints(self) -> List[str]:
        """Q4: Any constraints?"""
        # Options: performance, security, compatibility, none
        return []

    def _ask_dependencies(self, scope: str, constraints: List[str]) -> List[str]:
        """Q5: New dependencies?"""
        return []

    def _ask_test_context(self) -> Optional[str]:
        """Q6 (optional): Existing tests to update?"""
        return None

    def _estimate_loc_simple(self) -> int:
        """Estimate LOC for single file change"""
        return 30

    def _estimate_loc_medium(self) -> int:
        """Estimate LOC for few files"""
        return 120

    def _estimate_loc_large(self) -> int:
        """Estimate LOC for many files"""
        return 300

    def _estimate_loc_module(self) -> int:
        """Estimate LOC for new module"""
        return 250

"""
wfc:consensus-review Mock - Simple review stub for testing wfc:implement

ELEGANT: Minimal mock that simulates real review behavior
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Any


class MockReview:
    """
    Mock implementation of wfc:consensus-review.

    Simulates multi-agent review with configurable behavior.
    """

    def __init__(self, mode: str = "pass"):
        """
        Initialize mock review.

        Args:
            mode: "pass" (always pass), "fail" (always fail), "random" (50/50)
        """
        self.mode = mode or os.getenv("WFC_MOCK_REVIEW_MODE", "pass")

    def review(self, files: List[str], properties: List[str],
               task_id: str = "TASK-XXX") -> Dict[str, Any]:
        """
        Perform mock review.

        Args:
            files: List of file paths to review
            properties: List of property IDs to verify
            task_id: Task being reviewed

        Returns:
            Mock review report
        """
        # Simulate review scoring
        if self.mode == "fail":
            return self._failing_review(files, properties, task_id)
        elif self.mode == "random":
            if random.random() < 0.5:
                return self._failing_review(files, properties, task_id)

        # Default: passing review
        return self._passing_review(files, properties, task_id)

    def _passing_review(self, files: List[str], properties: List[str],
                       task_id: str) -> Dict[str, Any]:
        """Generate passing review report."""
        return {
            "review_id": f"review-{task_id}-pass",
            "task_id": task_id,
            "status": "PASSED",
            "score": 8.5,
            "agents": {
                "CR": {
                    "score": 9.0,
                    "findings": [
                        "Code logic is sound",
                        "Edge cases handled appropriately",
                        "Follows ELEGANT principles"
                    ]
                },
                "SEC": {
                    "score": 8.0,
                    "findings": [
                        "No critical vulnerabilities detected",
                        "Suggestion: Consider additional input validation"
                    ]
                },
                "PERF": {
                    "score": 8.5,
                    "findings": [
                        "Performance is acceptable",
                        "Minor optimization opportunity in loop"
                    ]
                },
                "COMP": {
                    "score": 9.0,
                    "findings": [
                        "All acceptance criteria met",
                        f"All {len(properties)} properties satisfied"
                    ]
                }
            },
            "files_reviewed": files,
            "properties_verified": properties,
            "consensus": "Code meets quality standards. Ready to merge.",
            "passed": True,
            "retry_count": 0
        }

    def _failing_review(self, files: List[str], properties: List[str],
                       task_id: str) -> Dict[str, Any]:
        """Generate failing review report."""
        return {
            "review_id": f"review-{task_id}-fail",
            "task_id": task_id,
            "status": "FAILED",
            "score": 6.0,
            "agents": {
                "CR": {
                    "score": 7.0,
                    "findings": [
                        "Logic issue in edge case handling",
                        "Missing null check in function"
                    ]
                },
                "SEC": {
                    "score": 5.0,
                    "findings": [
                        "CRITICAL: Potential SQL injection vector",
                        "Input validation insufficient"
                    ]
                },
                "PERF": {
                    "score": 7.0,
                    "findings": [
                        "Nested loop could be optimized",
                        "Consider caching result"
                    ]
                },
                "COMP": {
                    "score": 5.0,
                    "findings": [
                        f"Property {properties[0] if properties else 'PROP-001'} not verified",
                        "Missing test case for negative scenario"
                    ]
                }
            },
            "files_reviewed": files,
            "properties_verified": properties,
            "consensus": "Code has issues that must be addressed before merge.",
            "passed": False,
            "retry_count": 0,
            "required_fixes": [
                "Add null check in core function",
                "Fix SQL injection vulnerability",
                f"Add test for property {properties[0] if properties else 'PROP-001'}"
            ]
        }


# Convenience function
def mock_review(files: List[str], properties: List[str],
               task_id: str = "TASK-XXX", mode: str = "pass") -> Dict[str, Any]:
    """
    Perform mock review (convenience function).

    Args:
        files: Files to review
        properties: Properties to verify
        task_id: Task ID
        mode: Review mode (pass/fail/random)

    Returns:
        Mock review report
    """
    reviewer = MockReview(mode)
    return reviewer.review(files, properties, task_id)


if __name__ == "__main__":
    # Test mock review
    print("Testing mock review...")
    print()

    # Test passing review
    result = mock_review(
        files=["src/core.py", "tests/test_core.py"],
        properties=["PROP-001", "PROP-002"],
        task_id="TASK-002",
        mode="pass"
    )
    print(f"Pass mode: {result['status']} (score: {result['score']})")

    # Test failing review
    result = mock_review(
        files=["src/core.py"],
        properties=["PROP-001"],
        task_id="TASK-002",
        mode="fail"
    )
    print(f"Fail mode: {result['status']} (score: {result['score']})")
    print()
    print("✅ Mock review test passed")

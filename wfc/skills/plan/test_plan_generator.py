"""
TEST-PLAN.md Generator

Generates test plan from interview results and properties.
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
from .interview import InterviewResult


@dataclass
class TestCase:
    """Single test case"""
    id: str
    title: str
    description: str
    type: str  # unit, integration, e2e
    related_task: str
    related_property: str
    steps: List[str]
    expected: str


class TestPlanGenerator:
    """
    Generates TEST-PLAN.md from interview results.

    Creates test strategy and specific test cases.
    """

    def __init__(self, interview_result: InterviewResult):
        self.result = interview_result
        self.test_cases: List[TestCase] = []
        self.test_counter = 1

    def generate(self) -> str:
        """Generate complete TEST-PLAN.md content"""
        self._create_test_cases()
        return self._render_markdown()

    def _create_test_cases(self) -> None:
        """Create test cases from requirements and properties"""

        # Test cases from properties
        for idx, prop in enumerate(self.result.properties, start=1):
            self.test_cases.append(TestCase(
                id=self._next_id(),
                title=f"Verify {prop.get('type', 'property')}",
                description=f"Test that {prop.get('statement', '')}",
                type="integration",
                related_task="TBD",
                related_property=f"PROP-{idx:03d}",
                steps=[
                    "Setup test environment",
                    "Execute test scenario",
                    "Verify property holds"
                ],
                expected="Property is satisfied"
            ))

        # Test cases from requirements
        for idx, req in enumerate(self.result.requirements, start=1):
            if req.startswith("[Nice-to-have]"):
                continue

            self.test_cases.append(TestCase(
                id=self._next_id(),
                title=f"Test {req[:40]}...",
                description=f"Verify implementation of: {req}",
                type="unit",
                related_task=f"TASK-{idx+1:03d}",
                related_property="",
                steps=[
                    "Setup test data",
                    "Execute feature",
                    "Verify behavior"
                ],
                expected="Feature works as specified"
            ))

    def _next_id(self) -> str:
        """Generate next test case ID"""
        test_id = f"TEST-{self.test_counter:03d}"
        self.test_counter += 1
        return test_id

    def _render_markdown(self) -> str:
        """Render test plan as markdown"""
        lines = [
            "# Test Plan",
            "",
            "## Testing Strategy",
            "",
            f"**Testing Approach**: {self.result.raw_answers.get('testing_approach', 'TBD')}",
            f"**Coverage Target**: {self.result.raw_answers.get('coverage_target', 'TBD')}",
            "",
            "### Test Pyramid",
            "- **Unit Tests**: Test individual functions and classes",
            "- **Integration Tests**: Test component interactions",
            "- **E2E Tests**: Test complete user flows",
            "",
            "---",
            "",
            "## Test Cases",
            "",
        ]

        for test in self.test_cases:
            lines.extend([
                f"### {test.id}: {test.title}",
                f"- **Type**: {test.type}",
                f"- **Related Task**: {test.related_task}",
                f"- **Related Property**: {test.related_property}",
                f"- **Description**: {test.description}",
                "- **Steps**:",
            ])
            for step in test.steps:
                lines.append(f"  1. {step}")
            lines.extend([
                f"- **Expected**: {test.expected}",
                "",
            ])

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save TEST-PLAN.md to file"""
        content = self.generate()
        with open(path, 'w') as f:
            f.write(content)

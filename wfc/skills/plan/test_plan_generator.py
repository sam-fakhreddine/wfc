"""
TEST-PLAN.md Generator

Generates test plan from interview results and properties.
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
from .interview import InterviewResult
from .ears import EARSFormatter, EARSType


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
        """Create test cases from requirements and properties using EARS"""

        # Test cases from properties
        for idx, prop in enumerate(self.result.properties, start=1):
            prop_type = prop.get("type", "INVARIANT")
            statement = prop.get("statement", "")

            # Generate EARS-specific test steps
            steps = self._generate_ears_test_steps(prop_type, statement)

            self.test_cases.append(
                TestCase(
                    id=self._next_id(),
                    title=f"Verify {prop_type}: {statement[:40]}",
                    description=f"Test that {statement}",
                    type="integration",
                    related_task="TBD",
                    related_property=f"PROP-{idx:03d}",
                    steps=steps,
                    expected=f"{prop_type} property holds under all conditions",
                )
            )

        # Test cases from requirements
        for idx, req in enumerate(self.result.requirements, start=1):
            if req.startswith("[Nice-to-have]"):
                continue

            # Parse requirement to detect EARS type
            ears_req = EARSFormatter.parse_natural_language(req)
            steps = self._generate_ears_requirement_test_steps(ears_req)

            self.test_cases.append(
                TestCase(
                    id=self._next_id(),
                    title=f"Test {req[:40]}...",
                    description=f"Verify implementation of: {req}",
                    type="unit",
                    related_task=f"TASK-{idx+1:03d}",
                    related_property="",
                    steps=steps,
                    expected="Feature works as specified in EARS requirement",
                )
            )

    def _generate_ears_test_steps(self, prop_type: str, statement: str) -> List[str]:
        """Generate test steps based on EARS property type"""
        base_steps = ["Setup test environment"]

        if prop_type == "SAFETY":
            # UNWANTED behavior - test that it's prevented
            base_steps.extend(
                [
                    f"Attempt to trigger: {statement}",
                    "Verify system prevents the condition",
                    "Verify appropriate error/log is generated",
                    "Verify system state remains consistent",
                ]
            )
        elif prop_type == "LIVENESS":
            # EVENT_DRIVEN - test that it eventually happens
            base_steps.extend(
                [
                    "Trigger required condition",
                    f"Wait for: {statement}",
                    "Verify action completes within timeout",
                    "Verify no deadlock or starvation",
                ]
            )
        elif prop_type == "INVARIANT":
            # STATE_DRIVEN - test that it always holds
            base_steps.extend(
                [
                    "Execute multiple operations",
                    f"After each operation, verify: {statement}",
                    "Test under concurrent access",
                    "Verify invariant maintained throughout",
                ]
            )
        elif prop_type == "PERFORMANCE":
            # UBIQUITOUS - test performance bounds
            base_steps.extend(
                [
                    f"Execute operation: {statement}",
                    "Measure performance metrics",
                    "Verify metrics within acceptable bounds",
                    "Test under various load conditions",
                ]
            )
        else:
            base_steps.extend(["Execute test scenario", "Verify property holds"])

        return base_steps

    def _generate_ears_requirement_test_steps(self, ears_req) -> List[str]:
        """Generate test steps based on EARS requirement type"""
        steps = ["Setup test environment"]

        if ears_req.type == EARSType.EVENT_DRIVEN:
            steps.extend(
                [
                    f"Trigger event: {ears_req.trigger}",
                    f"Verify action: {ears_req.action}",
                    "Test with event occurring multiple times",
                    "Test with event NOT occurring (no action expected)",
                ]
            )
        elif ears_req.type == EARSType.STATE_DRIVEN:
            steps.extend(
                [
                    f"Establish state: {ears_req.state}",
                    f"Verify action occurs: {ears_req.action}",
                    f"Exit state: {ears_req.state}",
                    "Verify action stops when state changes",
                ]
            )
        elif ears_req.type == EARSType.UNWANTED:
            steps.extend(
                [
                    f"Attempt condition: {ears_req.condition}",
                    f"Verify prevention: {ears_req.action}",
                    "Verify system logs the attempt",
                    "Verify system recovers gracefully",
                ]
            )
        elif ears_req.type == EARSType.OPTIONAL:
            steps.extend(
                [
                    f"With feature enabled: {ears_req.feature}",
                    f"Verify action: {ears_req.action}",
                    f"With feature disabled: {ears_req.feature}",
                    "Verify graceful degradation",
                ]
            )
        else:  # UBIQUITOUS
            steps.extend(
                [
                    f"Execute: {ears_req.action}",
                    "Verify behavior is consistent",
                    "Test under normal and edge case conditions",
                ]
            )

        return steps

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
            lines.extend(
                [
                    f"### {test.id}: {test.title}",
                    f"- **Type**: {test.type}",
                    f"- **Related Task**: {test.related_task}",
                    f"- **Related Property**: {test.related_property}",
                    f"- **Description**: {test.description}",
                    "- **Steps**:",
                ]
            )
            for step in test.steps:
                lines.append(f"  1. {step}")
            lines.extend(
                [
                    f"- **Expected**: {test.expected}",
                    "",
                ]
            )

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save TEST-PLAN.md to file"""
        content = self.generate()
        with open(path, "w") as f:
            f.write(content)

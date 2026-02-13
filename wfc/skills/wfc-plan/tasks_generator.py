"""
TASKS.md Generator

Converts interview results into structured TASKS.md file.
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
from .interview import InterviewResult
from .ears import generate_acceptance_criteria_ears


@dataclass
class Task:
    """Single task in implementation plan"""

    id: str
    title: str
    description: str
    complexity: str  # S, M, L, XL
    dependencies: List[str]
    properties: List[str]
    files: List[str]
    acceptance_criteria: List[str]


class TasksGenerator:
    """
    Generates TASKS.md from interview results.

    ELEGANT: Simple task breakdown logic.
    MULTI-TIER: Logic layer only, no presentation.
    """

    def __init__(self, interview_result: InterviewResult):
        self.result = interview_result
        self.tasks: List[Task] = []
        self.task_counter = 1

    def generate(self) -> str:
        """Generate complete TASKS.md content"""
        # Break down requirements into tasks
        self._analyze_requirements()
        self._create_tasks()

        # Generate markdown
        return self._render_markdown()

    def _analyze_requirements(self) -> None:
        """Analyze requirements to determine task breakdown"""
        # This is simplified - real implementation would use LLM to intelligently break down
        pass

    def _create_tasks(self) -> None:
        """Create task list from requirements"""

        # Initial setup task (always first)
        self.tasks.append(
            Task(
                id=self._next_id(),
                title="Setup project structure",
                description="Create initial project structure, dependencies, and configuration",
                complexity="S",
                dependencies=[],
                properties=[],
                files=["README.md", "requirements.txt", "pyproject.toml"],
                acceptance_criteria=[
                    "Project structure follows best practices",
                    "All dependencies documented",
                    "Configuration files present",
                ],
            )
        )

        # Generate tasks from requirements
        for idx, req in enumerate(self.result.requirements, start=1):
            if req.startswith("[Nice-to-have]"):
                continue  # Skip nice-to-have for initial plan

            self.tasks.append(
                Task(
                    id=self._next_id(),
                    title=f"Implement {req[:50]}...",
                    description=req,
                    complexity=self._estimate_complexity(req),
                    dependencies=[self.tasks[0].id],  # Depend on setup
                    properties=self._match_properties(req),
                    files=[],  # Would be inferred
                    acceptance_criteria=self._generate_acceptance_criteria(req),
                )
            )

        # Final testing task
        self.tasks.append(
            Task(
                id=self._next_id(),
                title="End-to-end testing",
                description="Run complete integration and e2e tests",
                complexity="M",
                dependencies=[t.id for t in self.tasks[1:]],  # Depends on all implementation tasks
                properties=[],
                files=["tests/"],
                acceptance_criteria=[
                    "All tests pass",
                    "Coverage meets target",
                    "No critical issues",
                ],
            )
        )

    def _next_id(self) -> str:
        """Generate next task ID"""
        task_id = f"TASK-{self.task_counter:03d}"
        self.task_counter += 1
        return task_id

    def _estimate_complexity(self, requirement: str) -> str:
        """Estimate task complexity (S/M/L/XL)"""
        # Simplified heuristic - real implementation would be smarter
        word_count = len(requirement.split())
        if word_count < 10:
            return "S"
        elif word_count < 20:
            return "M"
        elif word_count < 40:
            return "L"
        else:
            return "XL"

    def _match_properties(self, requirement: str) -> List[str]:
        """Match requirement to properties"""
        matched = []
        for prop in self.result.properties:
            # Simple keyword matching - real implementation would be smarter
            if any(
                word in requirement.lower() for word in prop.get("statement", "").lower().split()
            ):
                matched.append(f"PROP-{len(matched)+1:03d}")
        return matched

    def _generate_acceptance_criteria(self, requirement: str) -> List[str]:
        """Generate EARS-formatted acceptance criteria for requirement"""
        # Use EARS format for clear, testable criteria
        return generate_acceptance_criteria_ears(requirement, system=self.result.goal or "system")

    def _render_markdown(self) -> str:
        """Render tasks as markdown"""
        lines = [
            "# Implementation Tasks",
            "",
            f"**Goal**: {self.result.goal}",
            "",
            f"**Context**: {self.result.context}",
            "",
            "---",
            "",
        ]

        for task in self.tasks:
            lines.extend(
                [
                    f"## {task.id}: {task.title}",
                    f"- **Complexity**: {task.complexity}",
                    f"- **Dependencies**: [{', '.join(task.dependencies)}]",
                    f"- **Properties**: [{', '.join(task.properties)}]",
                    f"- **Files**: {', '.join(task.files) if task.files else 'TBD'}",
                    f"- **Description**: {task.description}",
                    "- **Acceptance Criteria**:",
                ]
            )
            for criterion in task.acceptance_criteria:
                lines.append(f"  - [ ] {criterion}")
            lines.append("")

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save TASKS.md to file"""
        content = self.generate()
        with open(path, "w") as f:
            f.write(content)


# CLI for testing
if __name__ == "__main__":
    from interview import AdaptiveInterviewer

    interviewer = AdaptiveInterviewer()
    result = interviewer.run_interview()

    generator = TasksGenerator(result)
    print(generator.generate())

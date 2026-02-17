"""
Plan Orchestrator

Coordinates interview → generators → output files.
Maintains plan history with timestamped versions.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .architecture_designer import ArchitectureDesigner
from .interview import AdaptiveInterviewer, InterviewResult
from .plan_history import PlanHistory, create_plan_metadata
from .properties_generator import PropertiesGenerator
from .tasks_generator import TasksGenerator
from .test_plan_generator import TestPlanGenerator


@dataclass
class PlanResult:
    """Result of planning process"""

    interview_result: InterviewResult
    tasks_file: Path
    properties_file: Path
    test_plan_file: Path
    output_dir: Path
    architecture_approach: Optional[str] = None

    def __str__(self) -> str:
        arch_line = ""
        if self.architecture_approach:
            arch_line = f"\nArchitecture: {self.architecture_approach}"
        return f"""
Plan Complete!

Output Directory: {self.output_dir}
- TASKS.md: {self.tasks_file}
- PROPERTIES.md: {self.properties_file}
- TEST-PLAN.md: {self.test_plan_file}
- ARCHITECTURE-OPTIONS.md: {self.output_dir / "ARCHITECTURE-OPTIONS.md"}

Goal: {self.interview_result.goal}{arch_line}
Tasks: {self.tasks_file.read_text(encoding='utf-8').count('## TASK-')} tasks
Properties: {self.properties_file.read_text(encoding='utf-8').count('## PROP-')} properties
Tests: {self.test_plan_file.read_text(encoding='utf-8').count('### TEST-')} test cases
"""


class PlanOrchestrator:
    """
    Orchestrates the planning process.

    Interview → Generate → Save → History

    Each plan gets a timestamped directory for version history.
    """

    def __init__(self, output_dir: Optional[Path] = None, use_history: bool = True):
        """
        Initialize orchestrator.

        Args:
            output_dir: Custom output directory (overrides history)
            use_history: Enable timestamped plan history (default: True)
        """
        self.use_history = use_history and output_dir is None

        if self.use_history:
            # Use plan history system
            self.plan_history = PlanHistory()
            self.output_dir = None  # Will be set during run()
        else:
            # Use fixed directory (backward compatibility)
            self.output_dir = output_dir or Path("./plan")
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.plan_history = None

    def run(self) -> PlanResult:
        """
        Run complete planning process.

        Returns PlanResult with paths to generated files.
        """

        # Step 1: Interview
        interviewer = AdaptiveInterviewer()
        interview_result = interviewer.run_interview()

        # Determine output directory
        if self.use_history:
            # Generate timestamped directory
            self.output_dir = self.plan_history.get_next_plan_dir(goal=interview_result.goal)
            print(f"\n📁 Plan directory: {self.output_dir.name}")
        else:
            # Use fixed directory
            pass  # Already set in __init__

        # Save interview results
        interview_file = self.output_dir / "interview-results.json"
        interview_result.save(interview_file)

        # Step 1.5: Architecture Design
        designer = ArchitectureDesigner()
        approaches = designer.design(
            goal=interview_result.goal,
            context=interview_result.context,
        )
        comparison = designer.format_comparison(approaches)

        # Save architecture options
        arch_file = self.output_dir / "ARCHITECTURE-OPTIONS.md"
        with open(arch_file, "w") as f:
            f.write(comparison)
        print(f"  Created: {arch_file.name}")

        # Step 2: Generate TASKS.md
        tasks_gen = TasksGenerator(interview_result)
        tasks_file = self.output_dir / "TASKS.md"
        tasks_gen.save(tasks_file)

        # Step 3: Generate PROPERTIES.md
        props_gen = PropertiesGenerator(interview_result)
        props_file = self.output_dir / "PROPERTIES.md"
        props_gen.save(props_file)

        # Step 4: Generate TEST-PLAN.md
        test_gen = TestPlanGenerator(interview_result)
        test_file = self.output_dir / "TEST-PLAN.md"
        test_gen.save(test_file)

        # Step 5: Record in history (if enabled)
        if self.use_history:
            # Count tasks, properties, tests
            task_count = len(
                [
                    line
                    for line in tasks_file.read_text().splitlines()
                    if line.startswith("## TASK-")
                ]
            )
            prop_count = len(
                [
                    line
                    for line in props_file.read_text().splitlines()
                    if line.startswith("## PROP-")
                ]
            )
            test_count = len(
                [
                    line
                    for line in test_file.read_text().splitlines()
                    if line.startswith("### TEST-")
                ]
            )

            metadata = create_plan_metadata(
                plan_id=self.output_dir.name,
                directory=self.output_dir,
                goal=interview_result.goal,
                context=interview_result.context,
                task_count=task_count,
                property_count=prop_count,
                test_count=test_count,
            )
            self.plan_history.add_to_history(metadata)

            # Generate history markdown
            history_md = self.plan_history.generate_history_markdown()
            history_file = self.plan_history.base_dir / "HISTORY.md"
            with open(history_file, "w") as f:
                f.write(history_md)

            print(f"✓ Added to plan history ({len(self.plan_history.load_history())} total plans)")

        return PlanResult(
            interview_result=interview_result,
            tasks_file=tasks_file,
            properties_file=props_file,
            test_plan_file=test_file,
            output_dir=self.output_dir,
        )


# CLI for testing
if __name__ == "__main__":
    orchestrator = PlanOrchestrator(Path("./test-plan-output"))
    result = orchestrator.run()
    print(result)

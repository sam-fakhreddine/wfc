"""
Plan Orchestrator

Coordinates interview → generators → output files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .interview import AdaptiveInterviewer, InterviewResult
from .tasks_generator import TasksGenerator
from .properties_generator import PropertiesGenerator
from .test_plan_generator import TestPlanGenerator


@dataclass
class PlanResult:
    """Result of planning process"""
    interview_result: InterviewResult
    tasks_file: Path
    properties_file: Path
    test_plan_file: Path
    output_dir: Path

    def __str__(self) -> str:
        return f"""
Plan Complete!

Output Directory: {self.output_dir}
- TASKS.md: {self.tasks_file}
- PROPERTIES.md: {self.properties_file}
- TEST-PLAN.md: {self.test_plan_file}

Goal: {self.interview_result.goal}
Tasks: {len(open(self.tasks_file).read().count('## TASK-'))} tasks
Properties: {len(open(self.properties_file).read().count('## PROP-'))} properties
Tests: {len(open(self.test_plan_file).read().count('### TEST-'))} test cases
"""


class PlanOrchestrator:
    """
    Orchestrates the planning process.

    Interview → Generate → Save
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("./plan")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> PlanResult:
        """
        Run complete planning process.

        Returns PlanResult with paths to generated files.
        """

        # Step 1: Interview
        interviewer = AdaptiveInterviewer()
        interview_result = interviewer.run_interview()

        # Save interview results
        interview_file = self.output_dir / "interview-results.json"
        interview_result.save(interview_file)

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

        return PlanResult(
            interview_result=interview_result,
            tasks_file=tasks_file,
            properties_file=props_file,
            test_plan_file=test_file,
            output_dir=self.output_dir
        )


# CLI for testing
if __name__ == "__main__":
    orchestrator = PlanOrchestrator(Path("./test-plan-output"))
    result = orchestrator.run()
    print(result)

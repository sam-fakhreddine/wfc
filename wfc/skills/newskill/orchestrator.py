"""
NewSkill Orchestrator

Coordinates interview → prompt generation → auto-build.
"""

from pathlib import Path
from typing import Optional

from .interview import NewSkillInterviewer, SkillSpec
from .prompt_generator import PromptGenerator


class NewSkillOrchestrator:
    """
    Orchestrates skill creation.

    Interview → Prompt → (Optional) Auto-build
    """

    def __init__(self):
        self.interviewer = NewSkillInterviewer()
        self.generator = PromptGenerator()

    def create_skill(self, output_dir: Path, auto_build: bool = False) -> SkillSpec:
        """
        Create new skill.

        Returns SkillSpec with prompt path.
        """

        # Step 1: Interview
        spec = self.interviewer.run_interview()

        # Step 2: Generate prompt
        prompt_path = output_dir / f"{spec.name}-prompt.md"
        self.generator.save(spec, prompt_path)

        # Step 3: Auto-build (if requested)
        if auto_build:
            self._auto_build(spec, output_dir)

        return spec

    def _auto_build(self, spec: SkillSpec, output_dir: Path) -> None:
        """
        Auto-build skill using wfc-plan → wfc-implement.

        This would call the real plan and implement skills.
        """
        # Simplified - real implementation would:
        # 1. Call wfc-plan with spec as input
        # 2. Call wfc-implement with generated TASKS.md
        # 3. Register the new skill
        pass

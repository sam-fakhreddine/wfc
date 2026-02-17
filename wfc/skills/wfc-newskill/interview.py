"""
New Skill Interview System

Gathers requirements for building a new WFC skill.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SkillSpec:
    """Specification for a new skill"""

    name: str
    description: str
    trigger: str  # /wfc-skillname
    purpose: str
    inputs: List[str]
    outputs: List[str]
    agents: Dict[str, Any]  # agent architecture
    integration: List[str]  # other skills it integrates with
    configuration: Dict[str, Any]
    telemetry: List[str]  # what to track
    properties: List[str]  # formal properties
    raw_answers: Dict[str, Any]


class NewSkillInterviewer:
    """
    Interviews user to gather skill requirements.

    Follows same adaptive pattern as wfc-plan.
    """

    def __init__(self):
        self.answers: Dict[str, Any] = {}

    def run_interview(self) -> SkillSpec:
        """Run skill interview"""
        # Simplified - real implementation would use AskUserQuestion
        self.answers = {
            "name": "example-skill",
            "description": "Example skill description",
            "trigger": "/wfc-example",
            "purpose": "Does something useful",
            "inputs": "Files, context",
            "outputs": "Reports, code",
            "agents": "No",
            "integration": "wfc-plan, wfc-implement",
            "configuration": "output_dir, enable_feature",
            "telemetry": "execution_time, success_rate",
            "properties": "None",
        }

        return self._parse_results()

    def _parse_results(self) -> SkillSpec:
        """Parse answers into SkillSpec"""
        return SkillSpec(
            name=self.answers.get("name", ""),
            description=self.answers.get("description", ""),
            trigger=self.answers.get("trigger", ""),
            purpose=self.answers.get("purpose", ""),
            inputs=self.answers.get("inputs", "").split(","),
            outputs=self.answers.get("outputs", "").split(","),
            agents=self._parse_agents(self.answers.get("agents", "")),
            integration=self.answers.get("integration", "").split(","),
            configuration=self._parse_config(self.answers.get("configuration", "")),
            telemetry=self.answers.get("telemetry", "").split(","),
            properties=self.answers.get("properties", "").split(","),
            raw_answers=self.answers,
        )

    def _parse_agents(self, agents_str: str) -> Dict[str, Any]:
        """Parse agent architecture"""
        if agents_str.lower() in ["no", "none", ""]:
            return {"count": 0, "architecture": "none"}
        return {"count": 1, "architecture": "single"}

    def _parse_config(self, config_str: str) -> Dict[str, Any]:
        """Parse configuration"""
        if not config_str:
            return {}
        return {key.strip(): "default_value" for key in config_str.split(",")}

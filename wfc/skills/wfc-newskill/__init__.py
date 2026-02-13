"""
wfc-newskill - Meta-Skill Builder

Builds new WFC skills through interview → prompt generation → auto-build.
"""

__version__ = "0.1.0"

from .interview import NewSkillInterviewer, SkillSpec
from .prompt_generator import PromptGenerator
from .orchestrator import NewSkillOrchestrator

__all__ = [
    "NewSkillInterviewer",
    "SkillSpec",
    "PromptGenerator",
    "NewSkillOrchestrator",
]

"""
wfc-newskill - Meta-Skill Builder

Builds new WFC skills through interview → prompt generation → auto-build.
"""

__version__ = "0.1.0"

from .interview import NewSkillInterviewer, SkillSpec
from .orchestrator import NewSkillOrchestrator
from .prompt_generator import PromptGenerator

__all__ = [
    "NewSkillInterviewer",
    "SkillSpec",
    "PromptGenerator",
    "NewSkillOrchestrator",
]

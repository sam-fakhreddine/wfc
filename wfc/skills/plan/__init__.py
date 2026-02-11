"""
wfc:plan - Adaptive Planning with Formal Properties

Converts requirements into structured implementation plans.
"""

__version__ = "0.1.0"

from .interview import AdaptiveInterviewer, InterviewResult, Question
from .tasks_generator import TasksGenerator, Task
from .properties_generator import PropertiesGenerator, Property
from .test_plan_generator import TestPlanGenerator, TestCase
from .orchestrator import PlanOrchestrator, PlanResult
from .cli import PlanCLI

# Keep mock for backwards compatibility
from .mock import generate_mock_plan, MOCK_TASKS, MOCK_PROPERTIES, MOCK_TEST_PLAN

__all__ = [
    "AdaptiveInterviewer",
    "InterviewResult",
    "Question",
    "TasksGenerator",
    "Task",
    "PropertiesGenerator",
    "Property",
    "TestPlanGenerator",
    "TestCase",
    "PlanOrchestrator",
    "PlanResult",
    "PlanCLI",
    "generate_mock_plan",
    "MOCK_TASKS",
    "MOCK_PROPERTIES",
    "MOCK_TEST_PLAN",
]

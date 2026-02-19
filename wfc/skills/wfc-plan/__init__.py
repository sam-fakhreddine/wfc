"""
wfc-plan - Adaptive Planning with Formal Properties

Converts requirements into structured implementation plans.
"""

__version__ = "0.1.0"

from .architecture_designer import ArchitectureApproach, ArchitectureDesigner
from .cli import PlanCLI
from .interview import AdaptiveInterviewer, InterviewResult, Question

# Keep mock for backwards compatibility
from .mock import (
    MOCK_PROPERTIES,
    MOCK_TASKS,
    MOCK_TEST_PLAN,
    generate_mock_plan,
)
from .orchestrator import PlanOrchestrator, PlanResult
from .properties_generator import PropertiesGenerator, Property
from .tasks_generator import Task, TasksGenerator
from .test_plan_generator import TestCase, TestPlanGenerator

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
    "ArchitectureDesigner",
    "ArchitectureApproach",
    "PlanCLI",
    "generate_mock_plan",
    "MOCK_TASKS",
    "MOCK_PROPERTIES",
    "MOCK_TEST_PLAN",
]

"""
wfc-validate - Thoughtful Advisor

Analyzes plans/ideas across 7 dimensions for smart decision-making.
"""

__version__ = "0.1.0"

from .analyzer import DimensionAnalysis, SmartAnalysis, ValidateAnalyzer, Verdict
from .orchestrator import ValidateOrchestrator

__all__ = [
    "DimensionAnalysis",
    "SmartAnalysis",
    "ValidateAnalyzer",
    "ValidateOrchestrator",
    "Verdict",
]

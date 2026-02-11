"""
wfc:isthissmart - Thoughtful Advisor

Analyzes plans/ideas across 7 dimensions for smart decision-making.
"""

__version__ = "0.1.0"

from .analyzer import IsThisSmartAnalyzer, SmartAnalysis, Verdict, DimensionAnalysis
from .orchestrator import IsThisSmartOrchestrator

__all__ = [
    "IsThisSmartAnalyzer",
    "SmartAnalysis",
    "Verdict",
    "DimensionAnalysis",
    "IsThisSmartOrchestrator",
]

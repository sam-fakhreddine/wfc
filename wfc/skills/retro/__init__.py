"""
wfc-retro - AI-Powered Retrospectives

Analyzes telemetry, identifies trends, detects bottlenecks, generates recommendations.
"""

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class RetroReport:
    """Retrospective report"""
    trends: List[Dict]
    bottlenecks: List[Dict]
    recommendations: List[str]
    metrics_summary: Dict

__all__ = ["RetroReport"]

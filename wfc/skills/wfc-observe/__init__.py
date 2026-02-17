"""
wfc-observe - Observability from Properties

Maps formal properties to observables, generates metrics, alerts, dashboards.
"""

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ObservabilityPlan:
    """Observability plan"""

    metrics: List[str]
    alerts: List[Dict]
    dashboards: List[Dict]
    property_mappings: Dict[str, List[str]]


__all__ = ["ObservabilityPlan"]

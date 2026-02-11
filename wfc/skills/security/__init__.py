"""
wfc:security - Security Analysis & Threat Modeling

STRIDE threat modeling, attack surface mapping, dependency scanning.
"""

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import List

@dataclass
class ThreatModel:
    """Security threat model"""
    threats: List[str]
    mitigations: List[str]
    attack_surface: List[str]
    vulnerabilities: List[str]

__all__ = ["ThreatModel"]

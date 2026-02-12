"""
wfc-architecture - Architecture Generation & Analysis

Generates architecture docs, C4 diagrams, ADRs from plans/code.
"""

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import List

@dataclass
class ArchitectureSpec:
    """Architecture specification"""
    system_name: str
    components: List[str]
    integrations: List[str]
    c4_diagram: str
    adrs: List[str]

__all__ = ["ArchitectureSpec"]

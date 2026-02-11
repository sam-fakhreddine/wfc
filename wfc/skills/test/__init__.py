"""
wfc:test - Test Generation from Properties

Property-based and requirement-based test generation.
"""

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import List

@dataclass
class TestSuite:
    """Generated test suite"""
    test_files: List[str]
    coverage: float
    properties_tested: List[str]

__all__ = ["TestSuite"]

"""
AST Analyzer for WFC Review.

Extract actionable metrics from Python code to provide reviewers
with supplemental context (complexity, dangerous patterns, hotspots).
"""

from .language_detection import get_language, is_python
from .metrics_extractor import (
    CallVisitor,
    ComplexityVisitor,
    FileMetrics,
    FunctionMetrics,
    NestingVisitor,
    analyze_file,
    analyze_function,
    summarize_for_reviewer,
)

__all__ = [
    "CallVisitor",
    "ComplexityVisitor",
    "FileMetrics",
    "FunctionMetrics",
    "NestingVisitor",
    "analyze_file",
    "analyze_function",
    "get_language",
    "is_python",
    "summarize_for_reviewer",
]

"""
AST Analyzer for WFC Review.

Extract actionable metrics from Python code to provide reviewers
with supplemental context (complexity, dangerous patterns, hotspots).
"""

from .language_detection import is_python
from .metrics_extractor import (
    FileAnalysisVisitor,
    FileMetrics,
    FunctionMetrics,
    UnifiedFunctionVisitor,
    analyze_file,
    analyze_function,
    summarize_for_reviewer,
)

__all__ = [
    "FileAnalysisVisitor",
    "FileMetrics",
    "FunctionMetrics",
    "UnifiedFunctionVisitor",
    "analyze_file",
    "analyze_function",
    "is_python",
    "summarize_for_reviewer",
]

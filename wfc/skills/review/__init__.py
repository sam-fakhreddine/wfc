"""
wfc:consensus-review - Multi-Agent Consensus Code Review

Four specialized agents review code and reach consensus decision.
"""

__version__ = "0.1.0"

from .agents import (
    CodeReviewAgent,
    SecurityAgent,
    PerformanceAgent,
    ComplexityAgent,
    AgentType,
    AgentReview,
    ReviewComment,
)
from .consensus import ConsensusAlgorithm, ConsensusResult
from .orchestrator import ReviewOrchestrator, ReviewRequest, ReviewResult

# Keep mock for backwards compatibility
from .mock import MockReview

__all__ = [
    "CodeReviewAgent",
    "SecurityAgent",
    "PerformanceAgent",
    "ComplexityAgent",
    "AgentType",
    "AgentReview",
    "ReviewComment",
    "ConsensusAlgorithm",
    "ConsensusResult",
    "ReviewOrchestrator",
    "ReviewRequest",
    "ReviewResult",
    "MockReview",
]

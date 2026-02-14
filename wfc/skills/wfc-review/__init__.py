"""
wfc-review - Multi-Agent Consensus Code Review

Four specialized agents review code and reach consensus decision.

NOTE: Full implementation is in wfc/scripts/skills/review/
This is the Agent Skills wrapper with SKILL.md metadata.
"""

__version__ = "0.1.0"

# Export mock for backward compatibility
# Full review implementation imported from wfc/scripts/skills/review/
from .mock import MockReview

__all__ = [
    "MockReview",
    "mock_review",  # Convenience alias
]

# Convenience alias for mock review function
mock_review = MockReview

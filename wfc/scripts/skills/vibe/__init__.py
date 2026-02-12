"""
WFC Vibe - Natural Brainstorming Mode

SOLID: Minimal state, clear separation of concerns
"""

from .session import VibeSession
from .detector import ScopeDetector

__all__ = ["VibeSession", "ScopeDetector"]

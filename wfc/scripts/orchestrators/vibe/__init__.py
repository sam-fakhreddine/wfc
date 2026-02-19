"""
WFC Vibe - Natural Brainstorming Mode

SOLID: Minimal state, clear separation of concerns
"""

from .detector import ScopeDetector
from .session import VibeSession

__all__ = ["VibeSession", "ScopeDetector"]

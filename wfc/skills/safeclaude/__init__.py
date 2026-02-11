"""
wfc:safeclaude - Project-Specific Safe Allowlist Generator

Scans project, generates safe command allowlist, eliminates approval friction.
"""

__version__ = "0.1.0"

from .scanner import ProjectScanner, ProjectProfile
from .allowlist import AllowlistGenerator, AllowlistCategories
from .generator import SettingsGenerator

__all__ = [
    "ProjectScanner",
    "ProjectProfile",
    "AllowlistGenerator",
    "AllowlistCategories",
    "SettingsGenerator",
]

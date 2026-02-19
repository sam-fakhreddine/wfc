"""
wfc-safeclaude - Project-Specific Safe Allowlist Generator

Scans project, generates safe command allowlist, eliminates approval friction.
"""

__version__ = "0.1.0"

from .allowlist import AllowlistCategories, AllowlistGenerator
from .generator import SettingsGenerator
from .scanner import ProjectProfile, ProjectScanner

__all__ = [
    "ProjectScanner",
    "ProjectProfile",
    "AllowlistGenerator",
    "AllowlistCategories",
    "SettingsGenerator",
]

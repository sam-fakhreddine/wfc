"""
WFC Skills - PEP 562 Import Bridge

PROBLEM: Python cannot import modules with hyphens in directory names.
   `import wfc.skills.wfc-implement`  # SyntaxError

SOLUTION: Use PEP 562 __getattr__ to provide underscored aliases.
   `from wfc.skills import wfc_implement`  # Works! ✅

WHY THIS APPROACH:
- ✅ Maintains Agent Skills naming (hyphens in SKILL.md, directories)
- ✅ Provides valid Python import paths (underscores)
- ✅ Lazy loading (only imports what's needed)
- ✅ PEP 562 compliant (Python 3.7+)
- ✅ No symlinks or directory renaming needed

BEST PRACTICE REFERENCE:
- PEP 8: Module names should use underscores
- PEP 562: __getattr__ for lazy imports and aliases
- Agent Skills: Skill names use hyphens (wfc-implement, not wfc_implement)
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

# Mapping of hyphenated directory names to underscored Python module names
# Format: "python_name": "directory_name"
_SKILL_ALIAS_MAP = {
    "wfc_architecture": "wfc-architecture",
    "wfc_build": "wfc-build",
    "wfc_implement": "wfc-implement",
    "wfc_init": "wfc-init",
    "wfc_isthissmart": "wfc-isthissmart",
    "wfc_newskill": "wfc-newskill",
    "wfc_observe": "wfc-observe",
    "wfc_plan": "wfc-plan",
    "wfc_playground": "wfc-playground",
    "wfc_pr_comments": "wfc-pr-comments",
    "wfc_retro": "wfc-retro",
    "wfc_review": "wfc-review",
    "wfc_rules": "wfc-rules",
    "wfc_safeclaude": "wfc-safeclaude",
    "wfc_safeguard": "wfc-safeguard",
    "wfc_security": "wfc-security",
    "wfc_test": "wfc-test",
    "wfc_vibe": "wfc-vibe",
}

# Cache for already imported modules
_imported_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """
    PEP 562 __getattr__ for lazy importing hyphenated skill modules.

    Called when an attribute is not found normally.
    Enables: from wfc.skills import wfc_implement

    Args:
        name: Module name being imported (e.g., "wfc_implement")

    Returns:
        The imported module

    Raises:
        AttributeError: If name is not in alias map
        ImportError: If the underlying module import fails
    """
    if name in _imported_cache:
        return _imported_cache[name]

    if name not in _SKILL_ALIAS_MAP:
        # Not a known skill alias - let Python raise AttributeError
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    # Map underscored name to hyphenated directory
    hyphenated_name = _SKILL_ALIAS_MAP[name]

    # Import using importlib to handle hyphenated directory
    try:
        # Import the hyphenated directory as a module
        # e.g., from "wfc-architecture" import module
        module = importlib.import_module(f".{hyphenated_name}", package="wfc.skills")

        # Register with both names in sys.modules for proper imports
        import sys
        full_hyphenated_name = f"wfc.skills.{hyphenated_name}"
        full_underscored_name = f"wfc.skills.{name}"
        top_level_underscored_name = name  # e.g., "wfc_implement"

        if full_underscored_name not in sys.modules:
            sys.modules[full_underscored_name] = module

        # Also register at top level for direct imports
        if top_level_underscored_name not in sys.modules:
            sys.modules[top_level_underscored_name] = module

        _imported_cache[name] = module
        return module
    except ImportError as e:
        raise ImportError(
            f"Failed to import {name} (from directory '{hyphenated_name}'): {e}"
        ) from e


def __dir__() -> list[str]:
    """
    Return list of available attributes for dir() and tab completion.
    Includes all aliased skill names.
    """
    return list(_SKILL_ALIAS_MAP.keys())


# Export list for __all__
__all__ = list(_SKILL_ALIAS_MAP.keys())


# Diagnostic function (optional, for debugging)
def list_skills() -> dict[str, str]:
    """
    Return mapping of all available skill aliases.

    Returns:
        Dict mapping underscored names to hyphenated directories
    """
    return _SKILL_ALIAS_MAP.copy()


# Verify skills directory exists
_skills_dir = Path(__file__).parent
if not _skills_dir.is_dir():
    raise ImportError(f"Skills directory not found: {_skills_dir}")


# Auto-discover any skills not in the map (for future-proofing)
for skill_dir in _skills_dir.iterdir():
    if skill_dir.is_dir() and skill_dir.name.startswith("wfc-"):
        # Convert hyphenated to underscored
        underscored = skill_dir.name.replace("-", "_")
        if underscored not in _SKILL_ALIAS_MAP:
            _SKILL_ALIAS_MAP[underscored] = skill_dir.name
            __all__.append(underscored)

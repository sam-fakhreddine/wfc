"""
WFC Skills - PEP 562 Import Bridge

PROBLEM: Python cannot import modules with hyphens in directory names.
   `import wfc.skills.wfc-implement`  # SyntaxError

SOLUTION: Use PEP 562 __getattr__ to provide underscored aliases.
   `from wfc.skills import wfc_implement`  # Works!

WHY THIS APPROACH:
- Maintains Agent Skills naming (hyphens in SKILL.md, directories)
- Provides valid Python import paths (underscores)
- Lazy loading (only imports what's needed)
- PEP 562 compliant (Python 3.7+)
- No symlinks or directory renaming needed

BEST PRACTICE REFERENCE:
- PEP 8: Module names should use underscores
- PEP 562: __getattr__ for lazy imports and aliases
- Agent Skills: Skill names use hyphens (wfc-implement, not wfc_implement)
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

_SKILL_ALIAS_MAP: dict[str, str] = {
    "wfc_architecture": "wfc-architecture",
    "wfc_build": "wfc-build",
    "wfc_implement": "wfc-implement",
    "wfc_init": "wfc-init",
    "wfc_validate": "wfc-validate",
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

_imported_cache: dict[str, Any] = {}


def _register_skill_module(name: str, module: Any) -> None:
    """Register an imported skill module in sys.modules.

    Registers under both ``wfc.skills.<name>`` (namespaced) and bare ``<name>``
    (top-level). The top-level registration is required for the two-step PEP 562
    import pattern::

        from wfc.skills import wfc_implement   # triggers __getattr__
        from wfc_implement.parser import X      # needs bare registration

    Without the top-level entry, Python cannot resolve sub-imports from the
    bare module name.
    """
    qualified_name = f"wfc.skills.{name}"
    if qualified_name not in sys.modules:
        sys.modules[qualified_name] = module
    if name not in sys.modules:
        sys.modules[name] = module


def _discover_skills(skills_dir: Path) -> None:
    """Auto-discover skill directories not yet in the alias map.

    Scans ``skills_dir`` for ``wfc-*`` subdirectories and adds any missing
    entries to ``_SKILL_ALIAS_MAP`` and ``__all__``.
    """
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and skill_dir.name.startswith("wfc-"):
            underscored = skill_dir.name.replace("-", "_")
            if underscored not in _SKILL_ALIAS_MAP:
                _SKILL_ALIAS_MAP[underscored] = skill_dir.name
                __all__.append(underscored)


def __getattr__(name: str) -> Any:
    """PEP 562 __getattr__ for lazy importing hyphenated skill modules.

    Called when an attribute is not found normally.
    Enables: ``from wfc.skills import wfc_implement``
    """
    if name in _imported_cache:
        return _imported_cache[name]

    if name not in _SKILL_ALIAS_MAP:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    hyphenated_name = _SKILL_ALIAS_MAP[name]

    try:
        module = importlib.import_module(f".{hyphenated_name}", package="wfc.skills")
        _register_skill_module(name, module)
        _imported_cache[name] = module
        return module
    except ImportError as e:
        raise ImportError(
            f"Failed to import {name} (from directory '{hyphenated_name}'): {e}"
        ) from e


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and tab completion."""
    return list(_SKILL_ALIAS_MAP.keys())


__all__ = list(_SKILL_ALIAS_MAP.keys())


def list_skills() -> dict[str, str]:
    """Return mapping of all available skill aliases."""
    return _SKILL_ALIAS_MAP.copy()


_skills_dir = Path(__file__).parent
if not _skills_dir.is_dir():
    raise ImportError(f"Skills directory not found: {_skills_dir}")

_discover_skills(_skills_dir)

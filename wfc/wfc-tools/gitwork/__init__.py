"""
wfc-tools/gitwork - Centralized Git API for WFC

All WFC skills use this tool for git operations.
No skill runs raw git commands - everything goes through gitwork.
"""

__version__ = "0.1.0"

from .api import branch, commit, history, hooks, merge, rollback, semver, worktree
from .config import GitworkConfig
from .router import ModelRouter

__all__ = [
    "branch",
    "commit",
    "worktree",
    "merge",
    "rollback",
    "history",
    "hooks",
    "semver",
    "GitworkConfig",
    "ModelRouter",
]

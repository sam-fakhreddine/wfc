"""
WFC Git Hooks

Soft enforcement with warnings (never blocks).
"""

from .pre_commit import pre_commit_hook
from .commit_msg import commit_msg_hook
from .pre_push import pre_push_hook
from .installer import HookInstaller

__all__ = [
    "pre_commit_hook",
    "commit_msg_hook",
    "pre_push_hook",
    "HookInstaller",
]

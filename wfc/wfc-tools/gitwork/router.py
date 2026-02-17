"""
Model routing for git operations

Simple operations use Haiku, complex operations use Sonnet/Opus.
"""

from typing import Dict

from .config import get_config


class ModelRouter:
    """Routes operations to appropriate models"""

    SIMPLE_OPS = {
        "branch.create",
        "branch.delete",
        "branch.list",
        "commit.create",
        "commit.validate_message",
        "worktree.create",
        "worktree.delete",
        "worktree.list",
        "merge.abort",
        "hooks.install",
        "semver.current",
    }

    COMPLEX_OPS = {
        "branch._classify_type",  # Type classification needs reasoning
        "worktree.conflicts",  # Conflict analysis
        "merge.execute",  # Pre-flight checks
        "rollback.plan",  # Recovery plan generation
        "history.search_content",  # Secrets scanning
        "semver.calculate",  # Commit analysis
    }

    def __init__(self):
        self.config = get_config()

    def route(self, operation: str) -> str:
        """Determine which model to use"""
        if operation in self.SIMPLE_OPS:
            return self.config.get("model_routing.simple_ops", "haiku")
        elif operation in self.COMPLEX_OPS:
            return self.config.get("model_routing.complex_ops", "sonnet")
        else:
            # Default to sonnet for unknown operations
            return "sonnet"

    def record_usage(self, operation: str, model: str, tokens: Dict) -> None:
        """Record model usage in telemetry"""
        # Would integrate with WFC telemetry system
        pass


# Singleton
_instance = None


def get_router() -> ModelRouter:
    """Get model router instance"""
    global _instance
    if _instance is None:
        _instance = ModelRouter()
    return _instance

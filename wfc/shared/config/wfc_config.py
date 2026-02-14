"""
WFC Configuration System - ELEGANT & SIMPLE

Handles global (~/.claude/wfc.config.json) and project-local (wfc.config.json)
configuration with deep merging. Project config overrides global.

Design principles:
- Single Responsibility: Config loading and merging only
- DRY: One place for config logic
- Simple: JSON files, dict merging, no magic
"""

import copy
import json
from pathlib import Path
from typing import Dict, Any, Optional


class WFCConfig:
    """
    WFC Configuration loader with global/project scope support.

    Priority (highest to lowest):
    1. Project config (./wfc.config.json or <project_root>/wfc.config.json)
    2. Global config (~/.claude/wfc.config.json)
    3. Defaults (built-in)
    """

    PROJECT_CONFIG_NAME = "wfc.config.json"

    @staticmethod
    def _global_config_path() -> Path:
        """Compute global config path at call time (not import time)."""
        return Path.home() / ".claude" / "wfc.config.json"

    @staticmethod
    def _defaults() -> Dict[str, Any]:
        """Return default config with dynamic home directory resolution."""
        home = Path.home()
        return {
            "version": "1.0.0",
            "metrics": {
                "enabled": True,
                "directory": str(home / ".claude" / "metrics"),
                "format": "jsonl",
            },
            "llm": {
                "default_model": "claude-sonnet-4-20250514",
                "default_provider": "anthropic",
                "models": {
                    "sonnet": "claude-sonnet-4-20250514",
                    "opus": "claude-opus-4-20250514",
                    "haiku": "claude-haiku-4-5-20251001",
                },
            },
            "personas": {
                "enabled": True,
                "directory": str(home / ".claude" / "skills" / "wfc" / "personas"),
                "num_reviewers": 5,
                "require_diversity": True,
                "min_relevance_score": 0.3,
                "synthesis": {
                    "consensus_threshold": 3,
                    "weight_by_relevance": True,
                    "detect_unique_insights": True,
                    "detect_divergent_views": True,
                },
                "selection": {
                    "tech_stack_weight": 0.4,
                    "property_weight": 0.3,
                    "complexity_weight": 0.15,
                    "task_type_weight": 0.1,
                    "domain_weight": 0.05,
                },
            },
            "entire_io": {
                "enabled": True,  # ON BY DEFAULT: Privacy-first, local-only session capture
                "local_only": True,
                "create_checkpoints": True,
                "checkpoint_phases": [
                    "UNDERSTAND",
                    "TEST_FIRST",
                    "IMPLEMENT",
                    "REFACTOR",
                    "QUALITY_CHECK",
                    "SUBMIT",
                ],
                "privacy": {
                    "redact_secrets": True,
                    "max_file_size": 100000,
                    "exclude_patterns": [
                        "*.env",
                        "*.key",
                        "*.pem",
                        "*secret*",
                        "*credential*",
                        ".claude/*",
                    ],
                    "capture_env": False,
                },
                "retention": {"max_sessions": 100, "auto_cleanup": True},
            },
            "merge": {
                "strategy": "pr",  # NEW DEFAULT (Phase 2): "pr" = GitHub PR workflow, "direct" = local merge
                "pr": {
                    "enabled": True,  # PR workflow enabled by default
                    "base_branch": "main",  # Target branch for PRs
                    "draft": True,  # Create draft PRs by default
                    "auto_push": True,  # Automatically push branch before creating PR
                    "require_gh_cli": True,  # Fail if gh CLI not available
                },
                "direct": {
                    "enabled": True,  # Direct merge still available as fallback
                    "cleanup_worktree": True,  # Clean up worktree after successful merge
                },
            },
            "workflow_enforcement": {
                "enabled": True,  # Workflow enforcement enabled by default
                "mode": "warning",  # "warning" = soft enforcement (warn, don't block), "strict" = block violations
                "track_violations": True,  # Log violations to telemetry
                "protected_branches": ["main", "master"],  # Branches that trigger warnings
                "require_wfc_origin": False,  # Don't enforce WFC-only commits (yet)
            },
            "build": {
                "max_questions": 5,  # Maximum questions in quick interview
                "auto_assess_complexity": True,  # Automatically assess complexity from interview
                "dry_run_default": False,  # Default to actual implementation (not dry-run)
                "xl_recommendation_threshold": 10,  # Files threshold for XL recommendation
                "interview_timeout_seconds": 30,  # Max time for interview (PROP-008)
                "enforce_tdd": True,  # Enforce TDD workflow (PROP-007)
                "enforce_quality_gates": True,  # Enforce quality checks (PROP-001)
                "enforce_review": True,  # Enforce consensus review (PROP-002)
                "auto_push": False,  # Never auto-push to remote (PROP-003)
            },
            "vibe": {
                "reminder_frequency": [8, 12],  # Reminder every 8-12 messages (randomized)
                "max_scope_suggestions": 1,  # Max 1 scope suggestion per conversation
                "context_summarization_timeout": 5000,  # Max 5s for summarization (PROP-007)
                "transition_preview": True,  # Show preview before transition
                "auto_detect_scope": True,  # Automatically detect growing scope
            },
        }

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            project_root: Optional project root directory. If None, uses current directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        Load configuration with priority: project > global > defaults.

        Returns:
            Merged configuration dictionary
        """
        if self._config is not None:
            return self._config

        # Start with defaults
        config = self._defaults()

        # Merge global config if it exists
        global_config = self._load_file(self._global_config_path())
        if global_config:
            config = self._deep_merge(config, global_config)

        # Merge project config if it exists
        project_config_path = self.project_root / self.PROJECT_CONFIG_NAME
        project_config = self._load_file(project_config_path)
        if project_config:
            config = self._deep_merge(config, project_config)

        self._config = config
        return config

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a config value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "metrics.enabled")
            default: Default value if key not found

        Returns:
            Config value or default

        Example:
            >>> config.get("llm.default_model")
            "claude-sonnet-4-20250514"
        """
        config = self.load()
        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set a config value using dot notation (runtime only, not persisted).

        Args:
            key_path: Dot-separated path (e.g., "entire_io.enabled")
            value: Value to set

        Example:
            >>> config.set("entire_io.enabled", True)
        """
        config = self.load()
        keys = key_path.split(".")

        # Navigate to parent dict
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        current[keys[-1]] = value

    def _load_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON config file if it exists."""
        if not path.exists():
            return None

        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            return None

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries. Override wins on conflicts.

        Args:
            base: Base dictionary
            override: Override dictionary (takes precedence)

        Returns:
            Merged dictionary
        """
        result = copy.deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = WFCConfig._deep_merge(result[key], value)
            else:
                # Override wins - deep copy to prevent shared references
                result[key] = copy.deepcopy(value)

        return result


# Convenience function for quick config access
def get_config(project_root: Optional[Path] = None) -> WFCConfig:
    """
    Get WFC configuration instance.

    Args:
        project_root: Optional project root directory

    Returns:
        WFCConfig instance
    """
    return WFCConfig(project_root)


if __name__ == "__main__":
    # Simple test
    config = get_config()
    print("WFC Config loaded:")
    print(f"  Default model: {config.get('llm.default_model')}")
    print(f"  Metrics enabled: {config.get('metrics.enabled')}")
    print(f"  Metrics directory: {config.get('metrics.directory')}")

"""
WFC Configuration System - ELEGANT & SIMPLE

Handles global (~/.claude/wfc.config.json) and project-local (wfc.config.json)
configuration with deep merging. Project config overrides global.

Design principles:
- Single Responsibility: Config loading and merging only
- DRY: One place for config logic
- Simple: JSON files, dict merging, no magic
"""

import json
import os
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

    GLOBAL_CONFIG_PATH = Path.home() / ".claude" / "wfc.config.json"
    PROJECT_CONFIG_NAME = "wfc.config.json"

    # Default configuration - kept minimal and sensible
    DEFAULTS: Dict[str, Any] = {
        "version": "1.0.0",
        "metrics": {
            "enabled": True,
            "directory": str(Path.home() / ".claude" / "metrics"),
            "format": "jsonl"
        },
        "llm": {
            "default_model": "claude-sonnet-4-20250514",
            "default_provider": "anthropic",
            "models": {
                "sonnet": "claude-sonnet-4-20250514",
                "opus": "claude-opus-4-20250514",
                "haiku": "claude-haiku-4-5-20251001"
            }
        },
        "personas": {
            "enabled": True,
            "directory": str(Path.home() / ".claude" / "skills" / "wfc" / "personas"),
            "num_reviewers": 5,
            "require_diversity": True,
            "min_relevance_score": 0.3,
            "synthesis": {
                "consensus_threshold": 3,
                "weight_by_relevance": True,
                "detect_unique_insights": True,
                "detect_divergent_views": True
            },
            "selection": {
                "tech_stack_weight": 0.4,
                "property_weight": 0.3,
                "complexity_weight": 0.15,
                "task_type_weight": 0.1,
                "domain_weight": 0.05
            }
        }
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
        config = self.DEFAULTS.copy()

        # Merge global config if it exists
        global_config = self._load_file(self.GLOBAL_CONFIG_PATH)
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

    def _load_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON config file if it exists."""
        if not path.exists():
            return None

        try:
            with open(path, 'r') as f:
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
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = WFCConfig._deep_merge(result[key], value)
            else:
                # Override wins
                result[key] = value

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

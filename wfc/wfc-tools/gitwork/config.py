"""
Gitwork configuration management
"""

import json
from pathlib import Path
from typing import Dict, Any


class GitworkConfig:
    """Configuration for gitwork"""
    
    DEFAULTS = {
        "branch": {
            "naming_pattern": "chore/TASK-{id}-{slug}",
            "protected_branches": ["main", "master", "develop", "production"]
        },
        "commit": {
            "format": "conventional",
            "require_task_ref": True,
            "require_property_ref": False
        },
        "merge": {
            "strategy": "ff-only",
            "require_rebase": True
        },
        "worktree": {
            "directory": ".worktrees",
            "cleanup_on_success": True
        },
        "model_routing": {
            "simple_ops": "haiku",
            "complex_ops": "sonnet"
        }
    }
    
    def __init__(self):
        self.config = self.DEFAULTS.copy()
        self._load()
    
    def _load(self):
        """Load config from file"""
        # Try project config first
        project_config = Path("wfc-gitwork.config.json")
        if project_config.exists():
            with open(project_config) as f:
                self.config.update(json.load(f))
            return
        
        # Try global config
        global_config = Path.home() / ".claude" / "wfc-gitwork.config.json"
        if global_config.exists():
            with open(global_config) as f:
                self.config.update(json.load(f))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default


# Singleton
_instance = None

def get_config() -> GitworkConfig:
    """Get gitwork config instance"""
    global _instance
    if _instance is None:
        _instance = GitworkConfig()
    return _instance

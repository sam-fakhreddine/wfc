"""
WFC Hook Infrastructure

Unified PreToolUse hook system for real-time security enforcement
and configurable rule evaluation.

Components:
  - pretooluse_hook: Main entry point (reads JSON from stdin, exits 0 or 2)
  - security_hook: Pattern-based security checker (loads patterns/*.json)
  - rule_engine: Configurable rule evaluator (loads .wfc/rules/*.md)
  - hook_state: Session-scoped state for deduplicating warnings
  - config_loader: YAML frontmatter parser for rule files
"""

from wfc.scripts.hooks.hook_state import HookState
from wfc.scripts.hooks.rule_engine import evaluate as rule_evaluate
from wfc.scripts.hooks.security_hook import check as security_check

__all__ = ["HookState", "security_check", "rule_evaluate"]

"""
Configurable rule engine for WFC PreToolUse hooks.

Evaluates user-defined rules from .wfc/rules/*.md files against tool inputs.
Rules use YAML frontmatter with conditions that support regex, contains,
equals, starts_with, and ends_with operators.

All regex compilation is cached via @lru_cache for performance.
"""

from __future__ import annotations

import logging
import re
import signal
import time
from functools import lru_cache
from pathlib import Path
from typing import Optional

from wfc.scripts.hooks.config_loader import load_rules

logger = logging.getLogger(__name__)

# Default rules directory (relative to project root)
DEFAULT_RULES_DIR = ".wfc/rules"

# Map of tool names to the fields they provide
TOOL_FIELD_MAP: dict[str, dict[str, str]] = {
    "Write": {
        "new_text": "content",
        "file_path": "file_path",
    },
    "Edit": {
        "new_text": "new_string",
        "file_path": "file_path",
    },
    "NotebookEdit": {
        "new_text": "new_source",
        "file_path": "notebook_path",
    },
    "Bash": {
        "command": "command",
    },
}


class RegexTimeout(Exception):
    """Raised when regex compilation or matching times out."""

    pass


def _regex_timeout_handler(signum, frame):
    raise RegexTimeout("Regex operation timed out")


@lru_cache(maxsize=128)
def _compile_regex(pattern: str, timeout_seconds: int = 1) -> Optional[re.Pattern]:
    """Compile a regex pattern with caching. Returns None on invalid or complex patterns."""
    try:
        old_handler = signal.signal(signal.SIGALRM, _regex_timeout_handler)
        signal.alarm(timeout_seconds)
        try:
            compiled = re.compile(pattern)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        return compiled
    except (re.error, RegexTimeout) as e:
        logger.debug("Regex pattern failed '%s': %s", pattern, e)
        return None


def _get_field_value(field_name: str, tool_name: str, tool_input: dict) -> Optional[str]:
    """
    Resolve a rule condition field to the actual value from tool_input.

    Supports virtual field names that map to different tool_input keys
    depending on the tool:
      - new_text -> content (Write), new_string (Edit), new_source (NotebookEdit)
      - file_path -> file_path (Write/Edit), notebook_path (NotebookEdit)
      - command -> command (Bash)
    """
    tool_fields = TOOL_FIELD_MAP.get(tool_name, {})

    # Check if this is a virtual field name
    actual_key = tool_fields.get(field_name, field_name)
    value = tool_input.get(actual_key)

    if value is not None:
        return str(value)

    # Fallback: try the field name directly
    value = tool_input.get(field_name)
    return str(value) if value is not None else None


def _evaluate_condition(condition: dict, tool_name: str, tool_input: dict) -> bool:
    """
    Evaluate a single rule condition against tool input.

    Condition format:
        field: str - field name to check (new_text, command, file_path)
        operator: str - comparison operator
        pattern/value: str - expected value or regex pattern

    Supported operators:
        regex_match - field matches regex pattern
        contains - field contains value (case-sensitive)
        not_contains - field does not contain value
        equals - field equals value exactly
        starts_with - field starts with value
        ends_with - field ends with value
    """
    field_name = condition.get("field", "")
    operator = condition.get("operator", "")
    expected = condition.get("pattern", condition.get("value", ""))

    if not field_name or not operator:
        return False

    actual = _get_field_value(field_name, tool_name, tool_input)
    if actual is None:
        return False

    if operator == "regex_match":
        compiled = _compile_regex(str(expected))
        if compiled is None:
            return False
        try:
            old_handler = signal.signal(signal.SIGALRM, _regex_timeout_handler)
            signal.alarm(1)
            try:
                result = bool(compiled.search(actual))
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            return result
        except RegexTimeout:
            logger.warning(
                "Regex match timed out for pattern: %s", str(expected)[:50]
            )
            return False

    elif operator == "contains":
        return str(expected) in actual

    elif operator == "not_contains":
        return str(expected) not in actual

    elif operator == "equals":
        return actual == str(expected)

    elif operator == "starts_with":
        return actual.startswith(str(expected))

    elif operator == "ends_with":
        return actual.endswith(str(expected))

    else:
        logger.debug("Unknown operator: %s", operator)
        return False


def _matches_event(rule: dict, tool_name: str) -> bool:
    """Check if a rule applies to the given tool (event type)."""
    event = rule.get("event", "")
    if not event:
        return True  # No event filter = matches all

    if event == "file" and tool_name in ("Write", "Edit", "NotebookEdit"):
        return True
    if event == "bash" and tool_name == "Bash":
        return True
    if event == "all":
        return True

    return False


_bypass_count = 0


def evaluate(
    input_data: dict,
    rules_dir: Optional[Path] = None,
) -> dict:
    """
    Evaluate all rules against tool input.

    Args:
        input_data: Dict with 'tool_name' and 'tool_input' from Claude Code.
        rules_dir: Path to rules directory. Defaults to .wfc/rules/ in CWD.

    Returns:
        {} if no rules triggered.
        {"decision": "block", "reason": "..."} if a blocking rule matched.
        {"decision": "warn", "reason": "..."} if a warning rule matched.
    """
    global _bypass_count
    try:
        return _evaluate_impl(input_data, rules_dir)
    except Exception as e:
        _bypass_count += 1
        logger.warning(
            "Hook bypass: rule_engine exception=%s time=%s bypass_count=%d",
            type(e).__name__,
            time.strftime("%Y-%m-%dT%H:%M:%S"),
            _bypass_count,
        )
        # CRITICAL: Never block due to rule engine bugs
        return {}


def _evaluate_impl(
    input_data: dict,
    rules_dir: Optional[Path] = None,
) -> dict:
    """Internal implementation of evaluate()."""
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if not tool_name or not tool_input:
        return {}

    if rules_dir is None:
        rules_dir = Path.cwd() / DEFAULT_RULES_DIR

    rules = load_rules(rules_dir)
    if not rules:
        return {}

    block_reasons: list[str] = []
    warn_reasons: list[str] = []

    for rule in rules:
        # Skip disabled rules
        if not rule.get("enabled", True):
            continue

        # Check event type match
        if not _matches_event(rule, tool_name):
            continue

        # Evaluate all conditions (AND logic - all must match)
        conditions = rule.get("conditions", [])
        if not conditions:
            continue

        all_match = True
        for condition in conditions:
            # Handle both dict conditions and list-of-dicts
            if isinstance(condition, dict):
                cond_dict = condition
            else:
                continue

            if not _evaluate_condition(cond_dict, tool_name, tool_input):
                all_match = False
                break

        if not all_match:
            continue

        # Rule matched - determine action
        action = rule.get("action", "warn")
        name = rule.get("name", "unnamed-rule")
        body = rule.get("body", "")
        reason_text = body if body else f"Rule '{name}' triggered"

        if action == "block":
            block_reasons.append(f"[{name}] {reason_text}")
        elif action == "warn":
            warn_reasons.append(f"[{name}] {reason_text}")

    # Blocks take priority
    if block_reasons:
        return {
            "decision": "block",
            "reason": "; ".join(block_reasons),
        }
    elif warn_reasons:
        return {
            "decision": "warn",
            "reason": "; ".join(warn_reasons),
        }

    return {}

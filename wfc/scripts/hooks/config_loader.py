"""
Configuration loader for WFC rule engine.

Loads rule definitions from .wfc/rules/*.md files.
Each rule is a Markdown file with YAML frontmatter defining the rule metadata
and a body containing the human-readable message.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from a markdown file.

    Expects content between --- markers at the start of the file.
    Uses a minimal parser to avoid requiring PyYAML as a dependency.

    Returns:
        (frontmatter_dict, body_text)
    """
    lines = text.strip().split("\n")

    if not lines or lines[0].strip() != "---":
        return {}, text

    # Find closing ---
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, text

    # Parse YAML-like frontmatter (simple key: value pairs)
    frontmatter: dict[str, Any] = {}
    current_key = ""
    current_list: list[dict] = []
    in_list = False

    for line in lines[1:end_idx]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check for list item (indented with -)
        if stripped.startswith("- ") and in_list:
            item_text = stripped[2:].strip()
            # Check if it's a dict-like item
            if ":" in item_text:
                item_dict = _parse_inline_dict(item_text)
                current_list.append(item_dict)
            else:
                current_list.append({"value": _parse_value(item_text)})
            continue

        # Check for key: value
        if ":" in stripped:
            # Save previous list if any
            if in_list and current_key:
                frontmatter[current_key] = current_list

            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value_str = stripped[colon_idx + 1 :].strip()

            if not value_str:
                # Start of a list or nested structure
                current_key = key
                current_list = []
                in_list = True
            else:
                in_list = False
                frontmatter[key] = _parse_value(value_str)

    # Save final list if any
    if in_list and current_key:
        frontmatter[current_key] = current_list

    # Body is everything after the closing ---
    body = "\n".join(lines[end_idx + 1 :]).strip()

    return frontmatter, body


def _parse_value(value_str: str) -> Any:
    """Parse a simple YAML value."""
    # Remove quotes
    if (value_str.startswith('"') and value_str.endswith('"')) or (
        value_str.startswith("'") and value_str.endswith("'")
    ):
        return value_str[1:-1]

    # Booleans
    if value_str.lower() in ("true", "yes"):
        return True
    if value_str.lower() in ("false", "no"):
        return False

    # Numbers
    try:
        return int(value_str)
    except ValueError:
        pass
    try:
        return float(value_str)
    except ValueError:
        pass

    # Inline list [a, b, c]
    if value_str.startswith("[") and value_str.endswith("]"):
        items = value_str[1:-1].split(",")
        return [_parse_value(item.strip()) for item in items if item.strip()]

    return value_str


def _parse_inline_dict(text: str) -> dict:
    """Parse a simple inline dict from 'key: value, key2: value2' format."""
    result: dict[str, Any] = {}
    # Split on commas that aren't inside quotes
    parts = text.split(",")
    for part in parts:
        part = part.strip()
        if ":" in part:
            colon_idx = part.index(":")
            key = part[:colon_idx].strip()
            val = part[colon_idx + 1 :].strip()
            result[key] = _parse_value(val)
    return result


def load_rules(rules_dir: Path) -> list[dict]:
    """
    Load all rule files from a directory.

    Args:
        rules_dir: Path to the rules directory (typically .wfc/rules/)

    Returns:
        List of rule dicts, each with frontmatter fields plus 'body' for the message.
        Returns empty list if directory doesn't exist or has no valid rules.
    """
    rules: list[dict] = []

    try:
        if not rules_dir.is_dir():
            return rules
    except OSError:
        return rules

    for rule_file in sorted(rules_dir.glob("*.md")):
        try:
            text = rule_file.read_text(encoding="utf-8")
            frontmatter, body = _parse_frontmatter(text)

            if not frontmatter:
                logger.debug("Skipping %s: no frontmatter", rule_file.name)
                continue

            # Validate required fields
            if "name" not in frontmatter:
                logger.warning("Skipping %s: missing 'name' field", rule_file.name)
                continue

            rule = {**frontmatter}
            rule["body"] = body
            rule["_source_file"] = str(rule_file)
            rules.append(rule)

        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Error reading rule file %s: %s", rule_file, e)
            continue

    return rules

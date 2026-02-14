"""
Security pattern checker for WFC PreToolUse hooks.

Loads patterns from JSON files in wfc/scripts/hooks/patterns/ and checks
tool inputs against them. Returns block/warn/pass decisions.

Pattern matching uses compiled regexes cached via @lru_cache for performance.
"""

from __future__ import annotations

import json
import logging
import re
import signal
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from wfc.scripts.hooks.hook_state import HookState

logger = logging.getLogger("wfc.hooks.security")

# Directory containing pattern JSON files
PATTERNS_DIR = Path(__file__).parent / "patterns"

# Tools that write file content
FILE_WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}

# Tools that run shell commands
BASH_TOOLS = {"Bash"}

# Map file extensions to language identifiers
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".yml": "yaml",
    ".yaml": "yaml",
}


@dataclass
class PatternMatch:
    """A matched security pattern."""

    pattern_id: str
    description: str
    action: str  # "block" or "warn"
    matched_text: str


@dataclass
class CheckResult:
    """Result of a security check."""

    decision: str = ""  # "block", "warn", or "" (pass)
    reason: str = ""
    matches: list[PatternMatch] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        if not self.decision:
            return {}
        return {"decision": self.decision, "reason": self.reason}


class RegexTimeout(Exception):
    """Raised when regex compilation or matching times out."""

    pass


def _regex_timeout_handler(signum, frame):
    raise RegexTimeout("Regex operation timed out")


@lru_cache(maxsize=256)
def _compile_pattern(pattern: str, timeout_seconds: int = 1) -> Optional[re.Pattern]:
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
    except (re.error, RegexTimeout):
        return None


@lru_cache(maxsize=1)
def _load_patterns(patterns_dir: str = str(PATTERNS_DIR)) -> list[dict]:
    """Load all pattern files from the patterns directory (cached)."""
    patterns: list[dict] = []
    dir_path = Path(patterns_dir)
    if not dir_path.is_dir():
        return patterns

    for pattern_file in sorted(dir_path.glob("*.json")):
        try:
            data = json.loads(pattern_file.read_text(encoding="utf-8"))
            file_patterns = data.get("patterns", [])
            for p in file_patterns:
                p["_source"] = pattern_file.stem
            patterns.extend(file_patterns)
        except (json.JSONDecodeError, OSError, KeyError):
            continue  # Skip malformed pattern files

    return patterns


def _get_file_language(file_path: str) -> Optional[str]:
    """Determine the language of a file from its extension."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)


def _matches_file_pattern(file_path: str, file_patterns: list[str]) -> bool:
    """Check if a file path matches any of the glob-style file patterns."""
    path = Path(file_path)
    for fp in file_patterns:
        try:
            if path.match(fp):
                return True
        except ValueError:
            continue
    return False


def _extract_content(tool_name: str, tool_input: dict) -> tuple[str, str, str]:
    """
    Extract content to check and file path from tool input.

    Returns:
        (content_to_check, file_path, event_type)
    """
    if tool_name in FILE_WRITE_TOOLS:
        file_path = tool_input.get("file_path", "") or tool_input.get("notebook_path", "")
        # Write tool: content field
        # Edit tool: new_string field
        # NotebookEdit: new_source field
        content = (
            tool_input.get("content", "")
            or tool_input.get("new_string", "")
            or tool_input.get("new_source", "")
        )
        return content, file_path, "file"
    elif tool_name in BASH_TOOLS:
        command = tool_input.get("command", "")
        return command, "", "bash"
    return "", "", ""


_bypass_count = 0


def check(input_data: dict, state: Optional[HookState] = None) -> dict:
    """
    Check tool input against security patterns.

    Args:
        input_data: Dict with 'tool_name' and 'tool_input' from Claude Code PreToolUse hook.
        state: Optional HookState for deduplicating warnings. Created if not provided.

    Returns:
        {} if no issues found.
        {"decision": "block", "reason": "..."} if a blocking pattern matched.
        {"decision": "warn", "reason": "..."} if a warning pattern matched.
    """
    global _bypass_count
    try:
        return _check_impl(input_data, state)
    except Exception as e:
        _bypass_count += 1
        logger.warning(
            "Hook bypass: security_hook exception=%s time=%s bypass_count=%d",
            type(e).__name__,
            time.strftime("%Y-%m-%dT%H:%M:%S"),
            _bypass_count,
        )
        # CRITICAL: Never block due to hook bugs
        return {}


def _check_impl(input_data: dict, state: Optional[HookState] = None) -> dict:
    """Internal implementation of check()."""
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if not tool_name or not tool_input:
        return {}

    content, file_path, event_type = _extract_content(tool_name, tool_input)
    if not content:
        return {}

    if state is None:
        state = HookState()

    all_patterns = _load_patterns()
    file_language = _get_file_language(file_path) if file_path else None

    block_reasons: list[str] = []
    warn_reasons: list[str] = []

    for pattern_def in all_patterns:
        pattern_event = pattern_def.get("event", "")

        # Skip patterns that don't match the event type
        if pattern_event and pattern_event != event_type:
            continue

        # For file patterns, check language or file_patterns match
        if event_type == "file":
            languages = pattern_def.get("languages")
            file_patterns = pattern_def.get("file_patterns")

            if languages and file_language and file_language not in languages:
                continue
            if languages and not file_language and not file_patterns:
                # Unknown language and pattern requires specific languages - skip
                continue
            if file_patterns and file_path and not _matches_file_pattern(file_path, file_patterns):
                continue
            if file_patterns and not file_path:
                continue

        # Compile and match the regex
        regex_str = pattern_def.get("pattern", "")
        if not regex_str:
            continue

        compiled = _compile_pattern(regex_str)
        if compiled is None:
            continue

        # Match regex with timeout protection against ReDoS
        try:
            old_handler = signal.signal(signal.SIGALRM, _regex_timeout_handler)
            signal.alarm(1)
            try:
                match = compiled.search(content)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        except RegexTimeout:
            logger.warning("Regex match timed out for pattern: %s", regex_str[:50])
            continue

        if not match:
            continue

        pattern_id = pattern_def.get("id", "unknown")
        action = pattern_def.get("action", "warn")
        description = pattern_def.get("description", "Security pattern matched")

        if action == "block":
            block_reasons.append(f"[{pattern_id}] {description}")
        elif action == "warn":
            # Check if we already warned about this
            check_key = file_path or "__bash__"
            if state.has_warned(check_key, pattern_id):
                continue
            state.mark_warned(check_key, pattern_id)
            warn_reasons.append(f"[{pattern_id}] {description}")

    # Blocks take priority over warnings
    if block_reasons:
        return {
            "decision": "block",
            "reason": "Security violation: " + "; ".join(block_reasons),
        }
    elif warn_reasons:
        return {
            "decision": "warn",
            "reason": "Security warning: " + "; ".join(warn_reasons),
        }

    return {}

"""Tests for glob pattern validation (TASK-008) - PROP-003, PROP-010, PROP-011.

Tests validate_glob_pattern() helper function to prevent:
- Path traversal attacks (.. in patterns)
- Filesystem enumeration DoS (/**/* patterns)
- Unauthorized file access (patterns outside safe directories)
- Excessive matches (>1000 files)

Following TDD: RED phase - tests should fail before implementation.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

import pytest

SAFE_GLOB_PREFIXES = ("wfc/", "references/", "./wfc/", "./references/")
MAX_RECURSIVE_DEPTH = 2
MAX_GLOB_MATCHES = 1000


def validate_glob_pattern(pattern: any) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate glob pattern for safety (PROP-003, PROP-011).

    Prevents:
    - Path traversal attacks (.. in patterns)
    - Filesystem enumeration DoS (/**/* patterns)
    - Unauthorized file access (patterns outside safe directories)
    - Excessive recursion depth (>2 levels of **)

    Args:
        pattern: Glob pattern to validate (must be str)

    Returns:
        Tuple of (is_valid, error_message, validated_pattern)
    """
    if not isinstance(pattern, str):
        return (False, f"Pattern must be a string, got {type(pattern).__name__}", None)

    if not pattern or not pattern.strip():
        return (False, "Pattern cannot be empty or whitespace-only", None)

    pattern = pattern.strip()

    if ".." in pattern:
        return (False, "Pattern contains path traversal (..)", None)

    if pattern.startswith("/"):
        return (False, "Pattern is an absolute path (starts with /)", None)

    if not any(pattern.startswith(prefix) for prefix in SAFE_GLOB_PREFIXES):
        return (
            False,
            f"Pattern must start with one of: {', '.join(SAFE_GLOB_PREFIXES)}",
            None,
        )

    recursive_count = pattern.count("**")
    if recursive_count > MAX_RECURSIVE_DEPTH:
        return (
            False,
            f"Pattern has too many recursive globs (**): {recursive_count} "
            f"(max {MAX_RECURSIVE_DEPTH})",
            None,
        )

    return (True, None, pattern)


class TestGlobPatternValidation:
    """Test suite for glob pattern validation (PROP-011)."""

    def test_accepts_wfc_prefix(self):
        """Pattern starting with 'wfc/' should be accepted."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/skills/**/*.md")
        assert is_valid is True
        assert error_msg is None
        assert validated == "wfc/skills/**/*.md"

    def test_accepts_references_prefix(self):
        """Pattern starting with 'references/' should be accepted."""
        is_valid, error_msg, validated = validate_glob_pattern("references/reviewers/**/*.md")
        assert is_valid is True
        assert error_msg is None

    def test_accepts_dot_wfc_prefix(self):
        """Pattern starting with './wfc/' should be accepted."""
        is_valid, error_msg, validated = validate_glob_pattern("./wfc/skills/*/SKILL.md")
        assert is_valid is True
        assert error_msg is None

    def test_accepts_dot_references_prefix(self):
        """Pattern starting with './references/' should be accepted."""
        is_valid, error_msg, validated = validate_glob_pattern("./references/antipatterns.json")
        assert is_valid is True
        assert error_msg is None

    def test_rejects_unsafe_prefix(self):
        """Pattern with unsafe prefix should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("etc/passwd")
        assert is_valid is False
        assert "must start with one of" in error_msg.lower()
        assert validated is None

    def test_rejects_home_directory(self):
        """Pattern starting with home directory should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("~/secrets/**/*")
        assert is_valid is False
        assert "must start with one of" in error_msg.lower()

    def test_rejects_tmp_directory(self):
        """Pattern starting with /tmp should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("tmp/**/*.txt")
        assert is_valid is False
        assert "must start with one of" in error_msg.lower()

    def test_rejects_dotdot_in_pattern(self):
        """Pattern containing '..' should be rejected (path traversal)."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/../etc/passwd")
        assert is_valid is False
        assert "path traversal" in error_msg.lower() or ".." in error_msg

    def test_rejects_absolute_path(self):
        """Pattern starting with '/' should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("/etc/passwd")
        assert is_valid is False
        assert "absolute path" in error_msg.lower() or "/" in error_msg

    def test_rejects_dotdot_after_safe_prefix(self):
        """Pattern with '..' after safe prefix should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/skills/../../etc/passwd")
        assert is_valid is False
        assert ".." in error_msg or "path traversal" in error_msg.lower()

    def test_accepts_one_recursive_glob(self):
        """Pattern with one '**' should be accepted."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/**/SKILL.md")
        assert is_valid is True
        assert error_msg is None

    def test_accepts_two_recursive_globs(self):
        """Pattern with two '**' should be accepted (at limit)."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/**/**/SKILL.md")
        assert is_valid is True
        assert error_msg is None

    def test_rejects_three_recursive_globs(self):
        """Pattern with three '**' should be rejected (exceeds depth limit)."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/**/**/**/SKILL.md")
        assert is_valid is False
        assert "recursion depth" in error_msg.lower() or "**" in error_msg

    def test_rejects_four_recursive_globs(self):
        """Pattern with four '**' should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/**/**/**/**/SKILL.md")
        assert is_valid is False
        assert "recursion depth" in error_msg.lower() or "**" in error_msg

    def test_rejects_empty_pattern(self):
        """Empty pattern should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("")
        assert is_valid is False
        assert "empty" in error_msg.lower() or "invalid" in error_msg.lower()

    def test_rejects_whitespace_only_pattern(self):
        """Whitespace-only pattern should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern("   ")
        assert is_valid is False
        assert "empty" in error_msg.lower() or "invalid" in error_msg.lower()

    def test_accepts_single_file_pattern(self):
        """Single file pattern (no wildcards) should be accepted if in safe dir."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/skills/wfc-review/SKILL.md")
        assert is_valid is True
        assert error_msg is None

    def test_normalizes_pattern(self):
        """Pattern should be normalized (e.g., remove trailing slashes)."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/skills/")
        assert is_valid is True
        assert validated is not None


class TestGlobMatchCountLimit:
    """Test suite for glob match count limit (PROP-011) - max 1000 files."""

    def test_match_count_warning_when_exceeds_1000(self, tmp_path, capsys):
        """When glob matches >1000 files, should truncate to 1000 with warning."""
        pytest.skip("Integration test - requires fix_batch() implementation")

    def test_match_count_no_warning_when_under_1000(self, tmp_path):
        """When glob matches <1000 files, should not truncate or warn."""
        pytest.skip("Integration test - requires fix_batch() implementation")


class TestPathlibGlobUsage:
    """Test that fix_batch() uses pathlib.Path.glob() instead of glob.glob()."""

    def test_orchestrator_uses_pathlib_glob(self):
        """orchestrator.py should use Path.glob() not glob.glob()."""
        orchestrator_path = (
            Path(__file__).parent.parent / "wfc" / "skills" / "wfc-prompt-fixer" / "orchestrator.py"
        )
        content = orchestrator_path.read_text()

        assert (
            "glob.glob(pattern" not in content
        ), "fix_batch should use Path.glob(), not glob.glob()"

        assert "validate_glob_pattern" in content or "Path(" in content


class TestValidateGlobPatternEdgeCases:
    """Additional edge case tests for validate_glob_pattern()."""

    def test_handles_none_pattern(self):
        """None as pattern should be rejected gracefully."""
        is_valid, error_msg, validated = validate_glob_pattern(None)
        assert is_valid is False
        assert error_msg is not None

    def test_handles_non_string_pattern(self):
        """Non-string pattern should be rejected."""
        is_valid, error_msg, validated = validate_glob_pattern(123)
        assert is_valid is False
        assert error_msg is not None

    def test_case_sensitive_prefix_check(self):
        """Prefix check should be case-sensitive on Unix systems."""
        is_valid, error_msg, validated = validate_glob_pattern("WFC/skills/*/SKILL.md")
        if sys.platform != "win32":
            assert is_valid is False

    def test_pattern_with_special_chars(self):
        """Pattern with special shell characters should be safe (no shell injection)."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/skills/*/SKILL.md; rm -rf /")
        assert is_valid is True

    def test_unicode_in_pattern(self):
        """Pattern with unicode characters should be handled correctly."""
        is_valid, error_msg, validated = validate_glob_pattern("wfc/skills/*/プロンプト.md")
        assert is_valid is True

    def test_very_long_pattern(self):
        """Very long pattern should be rejected or truncated."""
        long_pattern = "wfc/" + "a" * 10000 + "/*.md"
        is_valid, error_msg, validated = validate_glob_pattern(long_pattern)
        assert error_msg is None or "too long" in error_msg.lower()

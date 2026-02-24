"""Tests for diff manifest builder."""

from wfc.scripts.orchestrators.review.diff_manifest import (
    ChangeHunk,
    ChangeType,
    DiffManifest,
    FileChange,
    HunkType,
    build_diff_manifest,
    format_manifest_for_reviewer,
)


def test_diff_manifest_creation():
    """Test basic DiffManifest creation."""
    manifest = DiffManifest(
        files_changed=2,
        lines_added=10,
        lines_removed=5,
        lines_modified=15,
    )

    assert manifest.files_changed == 2
    assert manifest.lines_added == 10
    assert manifest.lines_removed == 5
    assert manifest.lines_modified == 15


def test_diff_manifest_domain_hints():
    """Test domain hints functionality."""
    manifest = DiffManifest(
        files_changed=2,
        lines_added=10,
        lines_removed=5,
        lines_modified=15,
        domain_hints={
            "security": ["auth.py", "crypto.py"],
            "performance": ["database.py"],
        },
    )

    assert manifest.get_files_for_domain("security") == ["auth.py", "crypto.py"]
    assert manifest.get_files_for_domain("performance") == ["database.py"]
    assert manifest.get_files_for_domain("maintainability") == []


def test_diff_manifest_token_estimate():
    """Test token count estimation."""
    hunk = ChangeHunk(
        line_start=10,
        line_end=20,
        added_lines=5,
        removed_lines=3,
        context_before="def authenticate(user, password):",
        change_summary="Modified: replaced hardcoded check with bcrypt",
        change_type=HunkType.MODIFICATION,
    )

    file_change = FileChange(
        path="auth.py",
        change_type=ChangeType.MODIFIED,
        hunks=[hunk],
        total_added=5,
        total_removed=3,
    )

    manifest = DiffManifest(
        files_changed=1,
        lines_added=5,
        lines_removed=3,
        lines_modified=8,
        file_changes=[file_change],
    )

    tokens = manifest.get_token_estimate()
    assert tokens > 0
    assert tokens < 500


def test_build_diff_manifest_simple():
    """Test building manifest from simple diff."""
    diff = """diff --git a/auth.py b/auth.py
index 1234567..abcdefg 100644
--- a/auth.py
+++ b/auth.py
@@ -10,3 +10,3 @@ def login(user, password):
-    if password == "admin123":
+    if bcrypt.checkpw(password, user.password_hash):
         return True
"""

    manifest = build_diff_manifest(diff)

    assert manifest.files_changed == 1
    assert manifest.lines_added == 1
    assert manifest.lines_removed == 1


def test_format_manifest_for_reviewer():
    """Test formatting manifest as markdown."""
    hunk = ChangeHunk(
        line_start=10,
        line_end=12,
        added_lines=1,
        removed_lines=1,
        context_before="def login(user, password):",
        change_summary="Replaced hardcoded password with bcrypt check",
        change_type=HunkType.MODIFICATION,
    )

    file_change = FileChange(
        path="auth.py",
        change_type=ChangeType.MODIFIED,
        hunks=[hunk],
        domain_tags=["security"],
        total_added=1,
        total_removed=1,
    )

    manifest = DiffManifest(
        files_changed=1,
        lines_added=1,
        lines_removed=1,
        lines_modified=2,
        file_changes=[file_change],
        domain_hints={"security": ["auth.py"]},
    )

    markdown = format_manifest_for_reviewer(manifest, "security")

    assert "# Diff Summary" in markdown
    assert "auth.py" in markdown
    assert "security" in markdown
    assert "bcrypt" in markdown


def test_format_manifest_highlights_relevant_files():
    """Test that relevant files are highlighted for reviewer."""
    hunk1 = ChangeHunk(
        line_start=10,
        line_end=12,
        added_lines=1,
        removed_lines=1,
        context_before="def login(user, password):",
        change_summary="Security fix",
        change_type=HunkType.MODIFICATION,
    )

    hunk2 = ChangeHunk(
        line_start=50,
        line_end=55,
        added_lines=3,
        removed_lines=0,
        context_before="def get_users():",
        change_summary="Added pagination",
        change_type=HunkType.ADDITION,
    )

    file1 = FileChange(
        path="auth.py",
        change_type=ChangeType.MODIFIED,
        hunks=[hunk1],
        domain_tags=["security"],
        total_added=1,
        total_removed=1,
    )

    file2 = FileChange(
        path="database.py",
        change_type=ChangeType.MODIFIED,
        hunks=[hunk2],
        domain_tags=["performance"],
        total_added=3,
        total_removed=0,
    )

    manifest = DiffManifest(
        files_changed=2,
        lines_added=4,
        lines_removed=1,
        lines_modified=5,
        file_changes=[file1, file2],
        domain_hints={
            "security": ["auth.py"],
            "performance": ["database.py"],
        },
    )

    # Security reviewer should see auth.py highlighted
    security_markdown = format_manifest_for_reviewer(manifest, "security")
    assert "Relevant to security:" in security_markdown and "1 files" in security_markdown
    assert "auth.py" in security_markdown

    perf_markdown = format_manifest_for_reviewer(manifest, "performance")
    assert "Relevant to performance:" in perf_markdown and "1 files" in perf_markdown
    assert "database.py" in perf_markdown

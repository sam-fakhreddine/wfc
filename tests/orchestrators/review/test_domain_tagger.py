"""Tests for domain tagger."""

from wfc.scripts.orchestrators.review.diff_manifest import ChangeHunk, HunkType
from wfc.scripts.orchestrators.review.domain_tagger import tag_file_domains


def test_tag_file_by_path_security():
    """Test tagging security domain by file path."""
    tags = tag_file_domains("src/auth/login.py", [])
    assert "security" in tags


def test_tag_file_by_path_performance():
    """Test tagging performance domain by file path."""
    tags = tag_file_domains("src/database/queries.py", [])
    assert "performance" in tags


def test_tag_file_by_path_correctness():
    """Test tagging correctness domain by file path."""
    tags = tag_file_domains("tests/test_validation.py", [])
    assert "correctness" in tags


def test_tag_file_by_path_reliability():
    """Test tagging reliability domain by file path."""
    tags = tag_file_domains("config/settings.py", [])
    assert "reliability" in tags


def test_tag_file_by_content_security():
    """Test tagging security domain by content keywords."""
    hunk = ChangeHunk(
        line_start=10,
        line_end=15,
        added_lines=3,
        removed_lines=1,
        context_before="def authenticate(user, password):",
        change_summary="Added bcrypt password hashing",
        change_type=HunkType.MODIFICATION,
        raw_diff_lines=["+    hashed = bcrypt.hashpw(password)"],
    )

    tags = tag_file_domains("src/utils.py", [hunk])
    assert "security" in tags


def test_tag_file_by_content_performance():
    """Test tagging performance domain by content keywords."""
    hunk = ChangeHunk(
        line_start=20,
        line_end=25,
        added_lines=2,
        removed_lines=0,
        context_before="def get_users():",
        change_summary="Added database query optimization",
        change_type=HunkType.ADDITION,
        raw_diff_lines=["+    users = User.objects.select_related('profile')"],
    )

    tags = tag_file_domains("src/views.py", [hunk])
    assert "performance" in tags


def test_tag_file_by_content_correctness():
    """Test tagging correctness domain by content keywords."""
    hunk = ChangeHunk(
        line_start=30,
        line_end=35,
        added_lines=3,
        removed_lines=0,
        context_before="def process_data(value):",
        change_summary="Added null check and validation",
        change_type=HunkType.ADDITION,
        raw_diff_lines=[
            "+    if value is None:",
            "+        raise ValueError('Value cannot be None')",
        ],
    )

    tags = tag_file_domains("src/processor.py", [hunk])
    assert "correctness" in tags


def test_tag_file_by_content_reliability():
    """Test tagging reliability domain by content keywords."""
    hunk = ChangeHunk(
        line_start=40,
        line_end=45,
        added_lines=4,
        removed_lines=0,
        context_before="def connect_db():",
        change_summary="Added connection retry logic",
        change_type=HunkType.ADDITION,
        raw_diff_lines=[
            "+    for retry in range(3):",
            "+        with connection_pool.get() as conn:",
            "+            return conn",
        ],
    )

    tags = tag_file_domains("src/db.py", [hunk])
    assert "reliability" in tags


def test_tag_file_multiple_domains():
    """Test tagging file with multiple relevant domains."""
    hunk1 = ChangeHunk(
        line_start=10,
        line_end=15,
        added_lines=2,
        removed_lines=0,
        context_before="def login(user, password):",
        change_summary="Added password validation",
        change_type=HunkType.ADDITION,
        raw_diff_lines=[
            "+    if not password:",
            "+        raise ValueError('Password required')",
        ],
    )

    hunk2 = ChangeHunk(
        line_start=20,
        line_end=25,
        added_lines=1,
        removed_lines=0,
        context_before="def authenticate():",
        change_summary="Added bcrypt hashing",
        change_type=HunkType.ADDITION,
        raw_diff_lines=["+    hash = bcrypt.hashpw(password)"],
    )

    tags = tag_file_domains("auth.py", [hunk1, hunk2])

    assert "security" in tags
    assert "correctness" in tags


def test_tag_file_structural_patterns():
    """Test tagging by structural patterns."""
    hunk = ChangeHunk(
        line_start=1,
        line_end=5,
        added_lines=3,
        removed_lines=0,
        context_before="",
        change_summary="Added imports",
        change_type=HunkType.ADDITION,
        raw_diff_lines=[
            "+import logging",
            "+from django.db import models",
        ],
    )

    tags = tag_file_domains("models.py", [hunk])

    assert "reliability" in tags


def test_tag_file_empty_hunks():
    """Test tagging file with no hunks."""
    tags = tag_file_domains("src/unknown.py", [])

    assert isinstance(tags, list)


def test_tag_file_returns_sorted():
    """Test that tags are returned in sorted order."""
    hunk = ChangeHunk(
        line_start=10,
        line_end=15,
        added_lines=5,
        removed_lines=0,
        context_before="def process():",
        change_summary="Complex change",
        change_type=HunkType.ADDITION,
        raw_diff_lines=[
            "+    password = input()",
            "+    query = 'SELECT * FROM users'",
            "+    if not value:",
            "+        raise Exception",
        ],
    )

    tags = tag_file_domains("processor.py", [hunk])

    if len(tags) > 1:
        assert tags == sorted(tags)

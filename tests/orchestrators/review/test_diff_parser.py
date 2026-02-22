"""Tests for diff parser."""

from wfc.scripts.orchestrators.review.diff_manifest import ChangeType, HunkType
from wfc.scripts.orchestrators.review.diff_parser import parse_diff


def test_parse_empty_diff():
    """Test parsing empty diff."""
    result = parse_diff("")
    assert result == []


def test_parse_simple_modification():
    """Test parsing simple file modification."""
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -10,3 +10,3 @@ def foo():
-    return "old"
+    return "new"
     pass
"""

    files = parse_diff(diff)

    assert len(files) == 1
    assert files[0].path == "test.py"
    assert files[0].change_type == ChangeType.MODIFIED
    assert files[0].total_added == 1
    assert files[0].total_removed == 1
    assert len(files[0].hunks) == 1
    assert files[0].hunks[0].change_type == HunkType.MODIFICATION


def test_parse_file_addition():
    """Test parsing new file."""
    diff = """diff --git a/new.py b/new.py
new file mode 100644
index 0000000..abcdefg
--- /dev/null
+++ b/new.py
@@ -0,0 +1,3 @@
+def new_function():
+    return True
+
"""

    files = parse_diff(diff)

    assert len(files) == 1
    assert files[0].path == "new.py"
    assert files[0].change_type == ChangeType.ADDED
    assert files[0].total_added == 3
    assert files[0].total_removed == 0


def test_parse_file_deletion():
    """Test parsing deleted file."""
    diff = """diff --git a/old.py b/old.py
deleted file mode 100644
index abcdefg..0000000
--- a/old.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_function():
-    return False
-
"""

    files = parse_diff(diff)

    assert len(files) == 1
    assert files[0].path == "old.py"
    assert files[0].change_type == ChangeType.DELETED
    assert files[0].total_added == 0
    assert files[0].total_removed == 3


def test_parse_multiple_hunks():
    """Test parsing file with multiple change hunks."""
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -10,2 +10,2 @@ def foo():
-    old1
+    new1
@@ -20,2 +20,2 @@ def bar():
-    old2
+    new2
"""

    files = parse_diff(diff)

    assert len(files) == 1
    assert len(files[0].hunks) == 2
    assert files[0].hunks[0].line_start == 10
    assert files[0].hunks[1].line_start == 20


def test_parse_multiple_files():
    """Test parsing diff with multiple files."""
    diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -10,1 +10,1 @@
-old1
+new1
diff --git a/file2.py b/file2.py
index 7654321..gfedcba 100644
--- a/file2.py
+++ b/file2.py
@@ -5,1 +5,1 @@
-old2
+new2
"""

    files = parse_diff(diff)

    assert len(files) == 2
    assert files[0].path == "file1.py"
    assert files[1].path == "file2.py"


def test_extract_function_context():
    """Test extracting function/class context from hunks."""
    diff = """diff --git a/auth.py b/auth.py
index 1234567..abcdefg 100644
--- a/auth.py
+++ b/auth.py
@@ -10,3 +10,3 @@ def authenticate(user, password):
-    if password == "admin":  # pragma: allowlist secret
+    if bcrypt.checkpw(password, user.hash):
         return True
"""

    files = parse_diff(diff)

    assert len(files) == 1
    hunk = files[0].hunks[0]
    assert "def authenticate" in hunk.context_before or "authenticate" in hunk.change_summary


def test_generate_change_summary():
    """Test change summary generation."""
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -10,1 +10,1 @@
-    return "old"
+    return "new"
"""

    files = parse_diff(diff)

    assert len(files) == 1
    hunk = files[0].hunks[0]
    assert hunk.change_summary
    assert (
        "old" in hunk.change_summary
        or "new" in hunk.change_summary
        or "Modified" in hunk.change_summary
    )


def test_parse_addition_hunk_type():
    """Test hunk type detection for additions."""
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -10,0 +10,2 @@
+    new_line_1
+    new_line_2
"""

    files = parse_diff(diff)
    hunk = files[0].hunks[0]
    assert hunk.change_type == HunkType.ADDITION
    assert hunk.added_lines == 2
    assert hunk.removed_lines == 0


def test_parse_deletion_hunk_type():
    """Test hunk type detection for deletions."""
    diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -10,2 +10,0 @@
-    old_line_1
-    old_line_2
"""

    files = parse_diff(diff)
    hunk = files[0].hunks[0]
    assert hunk.change_type == HunkType.DELETION
    assert hunk.added_lines == 0
    assert hunk.removed_lines == 2


def test_line_end_pure_deletion():
    """Test line_end calculation for pure deletion hunks."""
    diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -10,5 +10,3 @@ def foo():
     line1
     line2
-    line3
-    line4
-    line5
     line6
"""

    files = parse_diff(diff)
    assert len(files) == 1
    hunk = files[0].hunks[0]

    assert hunk.line_start == 10
    assert hunk.removed_lines == 3
    assert hunk.added_lines == 0
    assert hunk.line_end == 12, f"Expected line_end=12 for pure deletion, got {hunk.line_end}"


def test_line_end_unequal_modification():
    """Test line_end calculation when added_lines != removed_lines."""
    diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -20,2 +20,5 @@ def bar():
-    old_line1
-    old_line2
+    new_line1
+    new_line2
+    new_line3
+    new_line4
+    new_line5
"""

    files = parse_diff(diff)
    assert len(files) == 1
    hunk = files[0].hunks[0]

    assert hunk.line_start == 20
    assert hunk.removed_lines == 2
    assert hunk.added_lines == 5
    assert (
        hunk.line_end == 24
    ), f"Expected line_end=24 for unequal modification, got {hunk.line_end}"


def test_line_end_old_bug_demonstration():
    """Demonstrate the old bug where line_end only considered added_lines."""
    diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -30,5 +30,2 @@ def baz():
-    remove1
-    remove2
-    remove3
-    remove4
-    remove5
+    add1
+    add2
"""

    files = parse_diff(diff)
    assert len(files) == 1
    hunk = files[0].hunks[0]

    assert hunk.line_start == 30
    assert hunk.removed_lines == 5
    assert hunk.added_lines == 2
    assert hunk.line_end == 34, f"Old bug would give 31, correct value is 34, got {hunk.line_end}"

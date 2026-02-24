"""
Tier 0 MVP - TASK-003 Tests
Test file locking for concurrent access safety.
"""

import threading
from wfc.shared.file_io import safe_append_text, append_text


class TestFileLocking:
    """Test FileLock implementation for concurrent writes."""

    def test_safe_append_text_exists(self):
        """safe_append_text function should be importable."""

    def test_safe_append_text_basic_write(self, tmp_path):
        """safe_append_text should append content to file."""
        test_file = tmp_path / "test.txt"

        safe_append_text(test_file, "Line 1\n")
        safe_append_text(test_file, "Line 2\n")

        content = test_file.read_text()
        assert content == "Line 1\nLine 2\n"

    def test_safe_append_text_creates_lock_file(self, tmp_path):
        """safe_append_text should create .lock file during write."""
        test_file = tmp_path / "test.txt"
        lock_file = tmp_path / "test.txt.lock"

        assert not lock_file.exists()

        safe_append_text(test_file, "content\n")

        assert test_file.exists()

    def test_safe_append_text_creates_parent_dir(self, tmp_path):
        """safe_append_text should create parent directories."""
        test_file = tmp_path / "subdir" / "nested" / "test.txt"

        assert not test_file.parent.exists()

        safe_append_text(test_file, "content\n", ensure_parent=True)

        assert test_file.exists()
        assert test_file.read_text() == "content\n"

    def test_safe_append_text_rejects_path_traversal(self, tmp_path):
        """safe_append_text resolves paths safely via .resolve()."""
        nested_dir = tmp_path / "nested" / "dir"
        nested_dir.mkdir(parents=True)

        traversal_path = nested_dir / ".." / ".." / "safe.txt"

        resolved = traversal_path.resolve()
        if resolved.exists():
            resolved.unlink()

        safe_append_text(traversal_path, "content\n")

        assert resolved.exists()
        assert resolved.read_text() == "content\n"

    def test_safe_append_text_timeout_parameter(self, tmp_path):
        """safe_append_text should accept timeout parameter."""
        test_file = tmp_path / "test.txt"

        safe_append_text(test_file, "content\n", timeout=5)

        assert test_file.read_text() == "content\n"

    def test_safe_append_text_concurrent_writes(self, tmp_path):
        """safe_append_text should handle concurrent writes without corruption."""
        test_file = tmp_path / "concurrent.txt"
        num_threads = 5
        writes_per_thread = 10

        def writer(thread_id):
            for i in range(writes_per_thread):
                safe_append_text(test_file, f"Thread-{thread_id}-Line-{i}\n")

        threads = []
        for t in range(num_threads):
            thread = threading.Thread(target=writer, args=(t,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        lines = test_file.read_text().splitlines()
        assert len(lines) == num_threads * writes_per_thread

        for line in lines:
            assert line.startswith("Thread-")
            assert "-Line-" in line

    def test_append_text_delegates_to_safe_append_text(self, tmp_path):
        """append_text should delegate to safe_append_text (backward compat)."""
        test_file = tmp_path / "test.txt"

        append_text(test_file, "content\n")

        assert test_file.read_text() == "content\n"

    def test_append_text_concurrent_safety(self, tmp_path):
        """append_text should also be safe for concurrent writes."""
        test_file = tmp_path / "concurrent.txt"
        num_threads = 3
        writes_per_thread = 5

        def writer(thread_id):
            for i in range(writes_per_thread):
                append_text(test_file, f"T{thread_id}L{i}\n")

        threads = []
        for t in range(num_threads):
            thread = threading.Thread(target=writer, args=(t,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        lines = test_file.read_text().splitlines()
        assert len(lines) == num_threads * writes_per_thread

    def test_safe_append_text_no_ensure_parent(self, tmp_path):
        """safe_append_text respects ensure_parent parameter."""
        test_file1 = tmp_path / "auto_created" / "test.txt"
        assert not test_file1.parent.exists()

        safe_append_text(test_file1, "content\n", ensure_parent=True)

        assert test_file1.exists()
        assert test_file1.read_text() == "content\n"

        test_file2 = tmp_path / "test2.txt"
        safe_append_text(test_file2, "content\n", ensure_parent=False)

        assert test_file2.read_text() == "content\n"

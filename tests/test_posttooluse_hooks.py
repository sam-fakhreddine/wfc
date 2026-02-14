"""Tests for PostToolUse hooks: file_checker, tdd_enforcer, context_monitor."""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wfc" / "scripts" / "hooks"))

from _util import check_file_length, find_git_root
from _checkers.python import strip_python_comments
from _checkers.typescript import strip_typescript_comments, find_project_root
from _checkers.go import strip_go_comments
from tdd_enforcer import (
    should_skip,
    is_test_file,
    is_trivial_edit,
    has_python_test_file,
    has_typescript_test_file,
    has_go_test_file,
    has_related_failing_test,
)
from context_monitor import (
    THRESHOLD_WARN,
    THRESHOLD_STOP,
    THRESHOLD_CRITICAL,
    run_context_monitor,
)


class TestFileLength:
    """Test file length warnings."""

    def test_short_file_no_warning(self, tmp_path):
        f = tmp_path / "short.py"
        f.write_text("\n".join(f"line {i}" for i in range(100)))
        assert check_file_length(f) is False

    def test_warn_threshold(self, tmp_path, capsys):
        f = tmp_path / "medium.py"
        f.write_text("\n".join(f"line {i}" for i in range(350)))
        assert check_file_length(f) is True
        captured = capsys.readouterr()
        assert "GROWING LONG" in captured.err

    def test_critical_threshold(self, tmp_path, capsys):
        f = tmp_path / "long.py"
        f.write_text("\n".join(f"line {i}" for i in range(550)))
        assert check_file_length(f) is True
        captured = capsys.readouterr()
        assert "TOO LONG" in captured.err

    def test_nonexistent_file(self, tmp_path):
        f = tmp_path / "nope.py"
        assert check_file_length(f) is False


class TestStripPythonComments:
    """Test Python comment stripping."""

    def test_strips_inline_comment(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1  # set x\n")
        assert strip_python_comments(f) is True
        assert f.read_text() == "x = 1\n"

    def test_preserves_type_hint(self, tmp_path):
        f = tmp_path / "typed.py"
        f.write_text("x = []  # type: list[int]\n")
        assert strip_python_comments(f) is False

    def test_preserves_noqa(self, tmp_path):
        f = tmp_path / "noqa.py"
        f.write_text("import os  # noqa: F401\n")
        assert strip_python_comments(f) is False

    def test_preserves_todo(self, tmp_path):
        f = tmp_path / "todo.py"
        f.write_text("x = 1  # TODO: fix this\n")
        assert strip_python_comments(f) is False

    def test_preserves_shebang(self, tmp_path):
        f = tmp_path / "script.py"
        f.write_text("#!/usr/bin/env python3\nx = 1\n")
        assert strip_python_comments(f) is False

    def test_no_comments_no_change(self, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text("x = 1\ny = 2\n")
        assert strip_python_comments(f) is False

    def test_removes_standalone_comment_line(self, tmp_path):
        f = tmp_path / "standalone.py"
        f.write_text("x = 1\n# this is a comment\ny = 2\n")
        assert strip_python_comments(f) is True
        assert "this is a comment" not in f.read_text()


class TestStripTypescriptComments:
    """Test TypeScript comment stripping."""

    def test_strips_inline_comment(self, tmp_path):
        f = tmp_path / "code.ts"
        f.write_text("const x = 1; // set x\n")
        assert strip_typescript_comments(f) is True
        assert f.read_text() == "const x = 1;\n"

    def test_preserves_ts_directive(self, tmp_path):
        f = tmp_path / "directive.ts"
        f.write_text("// @ts-ignore\nconst x: any = 1;\n")
        assert strip_typescript_comments(f) is False

    def test_preserves_eslint_directive(self, tmp_path):
        f = tmp_path / "eslint.ts"
        f.write_text("// eslint-disable-next-line\nconst x = 1;\n")
        assert strip_typescript_comments(f) is False

    def test_preserves_url(self, tmp_path):
        f = tmp_path / "url.ts"
        f.write_text('const url = "https://example.com";\n')
        assert strip_typescript_comments(f) is False

    def test_no_comments_no_change(self, tmp_path):
        f = tmp_path / "clean.ts"
        f.write_text("const x = 1;\n")
        assert strip_typescript_comments(f) is False


class TestStripGoComments:
    """Test Go comment stripping."""

    def test_strips_inline_comment(self, tmp_path):
        f = tmp_path / "code.go"
        f.write_text("x := 1 // set x\n")
        assert strip_go_comments(f) is True
        assert f.read_text() == "x := 1\n"

    def test_preserves_nolint(self, tmp_path):
        f = tmp_path / "nolint.go"
        f.write_text("x := 1 // nolint:errcheck\n")
        assert strip_go_comments(f) is False

    def test_preserves_go_directive(self, tmp_path):
        f = tmp_path / "directive.go"
        f.write_text("//go:generate stringer\n")
        assert strip_go_comments(f) is False

    def test_preserves_url(self, tmp_path):
        f = tmp_path / "url.go"
        f.write_text('url := "https://example.com"\n')
        assert strip_go_comments(f) is False


class TestTDDEnforcerSkip:
    """Test TDD enforcer skip logic."""

    def test_skip_markdown(self):
        assert should_skip("/project/README.md") is True

    def test_skip_json(self):
        assert should_skip("/project/config.json") is True

    def test_skip_yaml(self):
        assert should_skip("/project/config.yaml") is True

    def test_skip_toml(self):
        assert should_skip("/project/pyproject.toml") is True

    def test_skip_infrastructure(self):
        assert should_skip("/project/terraform/main.tf") is True

    def test_skip_generated(self):
        assert should_skip("/project/generated/types.py") is True

    def test_skip_node_modules(self):
        assert should_skip("/project/node_modules/lib/index.js") is True

    def test_skip_migrations(self):
        assert should_skip("/project/migrations/0001_initial.py") is True

    def test_skip_development(self):
        assert should_skip("/project/.development/scratch/test.py") is True

    def test_no_skip_source(self):
        assert should_skip("/project/src/handler.py") is False

    def test_no_skip_ts_source(self):
        assert should_skip("/project/src/handler.ts") is False


class TestTDDEnforcerTestFile:
    """Test is_test_file detection."""

    def test_python_test_prefix(self):
        assert is_test_file("/project/tests/test_handler.py") is True

    def test_python_test_suffix(self):
        assert is_test_file("/project/tests/handler_test.py") is True

    def test_python_conftest(self):
        assert is_test_file("/project/tests/conftest.py") is True

    def test_ts_test(self):
        assert is_test_file("/project/src/handler.test.ts") is True

    def test_ts_spec(self):
        assert is_test_file("/project/src/handler.spec.ts") is True

    def test_tsx_test(self):
        assert is_test_file("/project/src/Component.test.tsx") is True

    def test_go_test(self):
        assert is_test_file("/project/pkg/handler_test.go") is True

    def test_not_test_file(self):
        assert is_test_file("/project/src/handler.py") is False

    def test_not_test_ts(self):
        assert is_test_file("/project/src/handler.ts") is False


class TestTDDEnforcerTrivialEdit:
    """Test trivial edit detection."""

    def test_import_edit_is_trivial(self):
        assert is_trivial_edit("Edit", {
            "old_string": "import os",
            "new_string": "import os\nimport sys",
        }) is True

    def test_constant_addition_is_trivial(self):
        assert is_trivial_edit("Edit", {
            "old_string": "MAX_RETRY = 3",
            "new_string": "MAX_RETRY = 3\nDEFAULT_TIMEOUT = 30",
        }) is True

    def test_line_removal_is_trivial(self):
        assert is_trivial_edit("Edit", {
            "old_string": "x = 1\ny = 2\nz = 3",
            "new_string": "x = 1\nz = 3",
        }) is True

    def test_function_change_not_trivial(self):
        assert is_trivial_edit("Edit", {
            "old_string": "def foo():\n    return 1",
            "new_string": "def foo():\n    return 2",
        }) is False

    def test_write_not_trivial(self):
        assert is_trivial_edit("Write", {
            "old_string": "x = 1",
            "new_string": "x = 2",
        }) is False

    def test_empty_strings_not_trivial(self):
        assert is_trivial_edit("Edit", {
            "old_string": "",
            "new_string": "",
        }) is False


class TestTDDEnforcerTestFileSearch:
    """Test finding related test files."""

    def test_python_test_sibling(self, tmp_path):
        src = tmp_path / "handler.py"
        src.write_text("def handle(): pass")
        test = tmp_path / "test_handler.py"
        test.write_text("def test_handle(): pass")
        assert has_python_test_file(str(src)) is True

    def test_python_no_test(self, tmp_path):
        src = tmp_path / "handler.py"
        src.write_text("def handle(): pass")
        assert has_python_test_file(str(src)) is False

    def test_python_test_in_tests_dir(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src = src_dir / "handler.py"
        src.write_text("def handle(): pass")
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test = tests_dir / "test_handler.py"
        test.write_text("def test_handle(): pass")
        assert has_python_test_file(str(src)) is True

    def test_typescript_test_sibling(self, tmp_path):
        src = tmp_path / "handler.ts"
        src.write_text("export function handle() {}")
        test = tmp_path / "handler.test.ts"
        test.write_text("test('handle', () => {})")
        assert has_typescript_test_file(str(src)) is True

    def test_tsx_test(self, tmp_path):
        src = tmp_path / "Component.tsx"
        src.write_text("export function Component() {}")
        test = tmp_path / "Component.test.tsx"
        test.write_text("test('Component', () => {})")
        assert has_typescript_test_file(str(src)) is True

    def test_go_test_sibling(self, tmp_path):
        src = tmp_path / "handler.go"
        src.write_text("package main")
        test = tmp_path / "handler_test.go"
        test.write_text("package main")
        assert has_go_test_file(str(src)) is True

    def test_go_no_test(self, tmp_path):
        src = tmp_path / "handler.go"
        src.write_text("package main")
        assert has_go_test_file(str(src)) is False


class TestPytestLastfailed:
    """Test pytest lastfailed cache detection."""

    def test_detects_failing_test(self, tmp_path):
        cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
        cache_dir.mkdir(parents=True)
        lastfailed = cache_dir / "lastfailed"
        lastfailed.write_text(json.dumps({
            "tests/test_handler.py::test_handle": True
        }))
        assert has_related_failing_test(str(tmp_path), str(tmp_path / "handler.py")) is True

    def test_no_failing_test(self, tmp_path):
        cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
        cache_dir.mkdir(parents=True)
        lastfailed = cache_dir / "lastfailed"
        lastfailed.write_text(json.dumps({
            "tests/test_other.py::test_other": True
        }))
        assert has_related_failing_test(str(tmp_path), str(tmp_path / "handler.py")) is False

    def test_no_cache_file(self, tmp_path):
        assert has_related_failing_test(str(tmp_path), str(tmp_path / "handler.py")) is False

    def test_empty_cache(self, tmp_path):
        cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
        cache_dir.mkdir(parents=True)
        lastfailed = cache_dir / "lastfailed"
        lastfailed.write_text(json.dumps({}))
        assert has_related_failing_test(str(tmp_path), str(tmp_path / "handler.py")) is False


class TestContextMonitorThresholds:
    """Test context monitor threshold values."""

    def test_warn_threshold(self):
        assert THRESHOLD_WARN == 80

    def test_stop_threshold(self):
        assert THRESHOLD_STOP == 90

    def test_critical_threshold(self):
        assert THRESHOLD_CRITICAL == 95

    def test_ordering(self):
        assert THRESHOLD_WARN < THRESHOLD_STOP < THRESHOLD_CRITICAL


class TestFindProjectRoot:
    """Test TypeScript project root detection."""

    def test_finds_package_json(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text("{}")
        src = tmp_path / "src" / "index.ts"
        src.parent.mkdir()
        src.write_text("")
        assert find_project_root(src) == tmp_path

    def test_no_package_json(self, tmp_path):
        src = tmp_path / "orphan.ts"
        src.write_text("")
        result = find_project_root(src)
        assert result is None or isinstance(result, Path)

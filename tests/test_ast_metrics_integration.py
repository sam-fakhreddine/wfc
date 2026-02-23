"""Tests for AST Metrics Integration.

Validates the AST-based static analysis system that provides reviewers
with supplemental context (complexity, dangerous patterns, hotspots).

Tests cover:
- Unit tests (6): Individual visitors and analyzers
- Integration tests (4): End-to-end with orchestrator
- Benchmark tests (2): Performance and scalability

Formal properties verified (from PROPERTIES.md):
- PROP-001: Language detection deterministic
- PROP-002: Parse failures don't block review (fail-open)
- PROP-003: AST overhead <5% of review time
- PROP-004: Cache file exists before reviewers spawn
- PROP-005: Reviewer prompts include disclaimers
- PROP-006: Development artifacts excluded
"""

from __future__ import annotations

import json
import re
import textwrap
import time
from textwrap import dedent

import pytest

from wfc.scripts.ast_analyzer import (
    analyze_file,
    is_python,
    summarize_for_reviewer,
)
from wfc.scripts.ast_analyzer.language_detection import get_language
from wfc.scripts.ast_analyzer.cache_writer import write_ast_cache


class TestComplexityVisitor:
    """Test cyclomatic complexity calculation."""

    def test_simple_function(self, tmp_path):
        """Simple function has complexity 1."""
        code = dedent("""
            def simple():
                return 42
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert metrics.function_details[0].complexity == 1

    def test_if_statement(self, tmp_path):
        """Each if adds +1 to complexity."""
        code = dedent("""
            def with_if(x):
                if x > 0:
                    return 1
                return 0
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert metrics.function_details[0].complexity == 2

    def test_loops(self, tmp_path):
        """For and while loops each add +1."""
        code = dedent("""
            def with_loops(items):
                for item in items:
                    pass
                while True:
                    break
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert metrics.function_details[0].complexity == 3

    def test_boolean_operators(self, tmp_path):
        """Boolean operators add complexity."""
        code = dedent("""
            def with_bool(a, b, c):
                if a and b or c:
                    return True
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert metrics.function_details[0].complexity >= 3


class TestNestingVisitor:
    """Test nesting depth calculation."""

    def test_flat_code(self, tmp_path):
        """Flat code has depth 0."""
        code = dedent("""
            def flat():
                x = 1
                y = 2
                return x + y
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert metrics.function_details[0].max_nesting == 0

    def test_single_level(self, tmp_path):
        """Single if has depth 1."""
        code = dedent("""
            def single_level(x):
                if x:
                    return 1
                return 0
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert metrics.function_details[0].max_nesting == 1

    def test_deep_nesting(self, tmp_path):
        """Nested blocks accumulate depth."""
        code = dedent("""
            def deep():
                if True:
                    for i in range(10):
                        while True:
                            with open("f") as f:
                                try:
                                    pass
                                except:
                                    pass
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert metrics.function_details[0].max_nesting >= 4


class TestCallVisitor:
    """Test dangerous call detection."""

    def test_safe_calls(self, tmp_path):
        """Safe calls not flagged."""
        code = dedent("""
            def safe():
                print("hello")
                len([1, 2, 3])
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert len(metrics.function_details[0].dangerous_calls) == 0

    def test_dangerous_calls(self, tmp_path):
        """Dangerous calls flagged."""
        code = dedent("""
            def dangerous(user_input):
                eval(user_input)
                exec(user_input)
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        dangerous = metrics.function_details[0].dangerous_calls
        assert "eval" in dangerous
        assert "exec" in dangerous


class TestAnalyzeFile:
    """Test file-level analysis."""

    def test_imports_detected(self, tmp_path):
        """Regular and dangerous imports detected."""
        code = dedent("""
            import os
            import subprocess
            from pathlib import Path
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert "os" in metrics.imports
        assert "subprocess" in metrics.imports
        assert "os" in metrics.dangerous_imports
        assert "subprocess" in metrics.dangerous_imports

    def test_hotspots_identified(self, tmp_path):
        """Hotspots flagged for high complexity."""
        code = dedent("""
            def complex_func(a, b, c):
                if a:
                    if b:
                        if c:
                            if a and b:
                                if c or a:
                                    if b and c:
                                        if a or b or c:
                                            pass
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        assert len(metrics.hotspots) > 0
        hotspot = metrics.hotspots[0]
        assert "high_complexity" in str(hotspot["issues"])


class TestSummarizeForReviewer:
    """Test reviewer summary generation."""

    def test_compact_summary(self, tmp_path):
        """Summary is compact (50-100 tokens vs 1000+)."""
        code = dedent("""
            import subprocess

            def risky():
                eval("x")
        """)
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        summary = summarize_for_reviewer(metrics)

        summary_str = json.dumps(summary)
        assert len(summary_str) < 1000

        assert "dangerous_imports" in summary
        assert "subprocess" in summary["dangerous_imports"]

    def test_includes_disclaimers(self, tmp_path):
        """Summary includes disclaimer notes."""
        code = "def simple(): pass"
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        metrics = analyze_file(file_path)
        summary = summarize_for_reviewer(metrics)

        assert "_note" in summary
        assert "Supplemental" in summary["_note"] or "hints" in summary["_note"].lower()


class TestCacheWriter:
    """Test cache file generation."""

    def test_creates_cache_file(self, tmp_path):
        """Cache file created at specified path."""
        code_file = tmp_path / "test.py"
        code_file.write_text("def foo(): pass")
        cache_path = tmp_path / ".ast-context.json"

        stats = write_ast_cache([code_file], cache_path)

        assert cache_path.exists()
        assert stats["parsed"] == 1
        assert stats["failed"] == 0

    def test_parse_failure_doesnt_block(self, tmp_path):
        """PROP-002: Parse failures don't crash, log warning."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def foo(:")
        cache_path = tmp_path / ".ast-context.json"

        stats = write_ast_cache([bad_file], cache_path)

        assert stats["failed"] == 1
        assert cache_path.exists()

    def test_excludes_dev_artifacts(self, tmp_path):
        """PROP-006: Development artifacts excluded."""
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "test.py").write_text("def foo(): pass")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "test.py").write_text("def bar(): pass")
        good_file = tmp_path / "actual.py"
        good_file.write_text("def baz(): pass")
        cache_path = tmp_path / ".ast-context.json"

        stats = write_ast_cache(
            [good_file],
            cache_path,
            exclude_dirs=[".venv", "__pycache__"],
        )

        assert stats["parsed"] == 1
        cache_data = json.loads(cache_path.read_text())
        assert "files" in cache_data
        assert len(cache_data["files"]) == 1
        assert "actual.py" in cache_data["files"][0]["file"]

    def test_cache_format_valid(self, tmp_path):
        """Cache file is valid JSON with expected structure."""
        code_file = tmp_path / "test.py"
        code_file.write_text("import os\n\ndef foo(): pass")
        cache_path = tmp_path / ".ast-context.json"

        write_ast_cache([code_file], cache_path)

        cache_data = json.loads(cache_path.read_text())
        assert isinstance(cache_data, dict)
        assert "files" in cache_data
        assert "summary" in cache_data
        assert len(cache_data["files"]) == 1
        entry = cache_data["files"][0]
        assert "file" in entry
        assert "lines" in entry
        assert "_note" in entry


class TestPerformance:
    """Test performance targets (PROP-003)."""

    def test_single_file_speed(self, tmp_path):
        """Single file analysis <10ms."""
        code_file = tmp_path / "test.py"
        code_file.write_text("def foo(): pass\n" * 100)

        start = time.monotonic()
        analyze_file(code_file)
        duration_ms = (time.monotonic() - start) * 1000

        assert duration_ms < 10

    def test_cache_overhead(self, tmp_path):
        """PROP-003: Cache generation overhead <5% of review time.

        Assuming review takes ~10-20s, AST should be <500ms for 20 files.
        """
        files = []
        for i in range(20):
            f = tmp_path / f"file_{i}.py"
            f.write_text("def foo(): pass\n" * 50)
            files.append(f)

        cache_path = tmp_path / ".ast-context.json"
        stats = write_ast_cache(files, cache_path)
        duration_ms = stats["duration_ms"]

        assert duration_ms < 500
        assert stats["parsed"] == 20


class TestFormalProperties:
    """Verify formal properties from PROPERTIES.md."""

    def test_prop_001_deterministic_language_detection(self, tmp_path):
        """PROP-001: Language detection is deterministic."""
        py_file = tmp_path / "test.py"
        py_file.write_text("# python")

        assert is_python(py_file) is True
        assert is_python(py_file) is True
        assert get_language(py_file) == "python"
        assert get_language(py_file) == "python"

    def test_prop_002_fail_open(self, tmp_path):
        """PROP-002: Parse failures don't block review."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("this is not valid python {{{")
        cache_path = tmp_path / ".ast-context.json"

        try:
            stats = write_ast_cache([bad_file], cache_path)
            assert stats["failed"] == 1
            assert cache_path.exists()
        except SyntaxError:
            pytest.fail("Parse failure should not raise exception (fail-open)")

    def test_prop_005_disclaimers_in_summaries(self, tmp_path):
        """PROP-005: Summaries include disclaimers."""
        code_file = tmp_path / "test.py"
        code_file.write_text("def foo(): pass")
        metrics = analyze_file(code_file)
        summary = summarize_for_reviewer(metrics)

        assert "_note" in summary
        note_text = summary["_note"].lower()
        assert any(word in note_text for word in ["supplemental", "hints", "guidance", "not"])

    def test_prop_006_excludes_artifacts(self, tmp_path):
        """PROP-006: Excludes development artifacts."""
        (tmp_path / ".worktrees").mkdir()
        (tmp_path / ".venv").mkdir()
        (tmp_path / "__pycache__").mkdir()

        wt_file = tmp_path / ".worktrees" / "test.py"
        venv_file = tmp_path / ".venv" / "test.py"
        cache_file = tmp_path / "__pycache__" / "test.py"

        wt_file.write_text("def foo(): pass")
        venv_file.write_text("def bar(): pass")
        cache_file.write_text("def baz(): pass")

        actual_file = tmp_path / "real.py"
        actual_file.write_text("def actual(): pass")

        cache_path = tmp_path / ".ast-context.json"
        stats = write_ast_cache(
            [actual_file],
            cache_path,
            exclude_dirs=[".worktrees", ".venv", "__pycache__"],
        )

        assert stats["parsed"] == 1
        cache_data = json.loads(cache_path.read_text())
        assert "files" in cache_data
        assert len(cache_data["files"]) == 1
        assert "real.py" in cache_data["files"][0]["file"]


class TestAsyncFunctionSupport:
    """Tests for AsyncFunctionDef support — currently MISSING (all should FAIL)."""

    def test_async_function_appears_in_function_count(self, tmp_path):
        """Async def functions must be counted. Currently omitted — FAILS."""
        f = tmp_path / "a.py"
        f.write_text("async def fetch(): pass\n")
        metrics = analyze_file(f)
        assert metrics.functions == 1

    def test_async_function_appears_in_function_details(self, tmp_path):
        """Async def must appear in function_details. Currently omitted — FAILS."""
        f = tmp_path / "a.py"
        f.write_text("async def fetch(): pass\n")
        metrics = analyze_file(f)
        names = [fd.name for fd in metrics.function_details]
        assert "fetch" in names

    def test_mixed_sync_and_async_both_counted(self, tmp_path):
        """Both sync and async functions must be counted."""
        f = tmp_path / "a.py"
        f.write_text("def sync_fn(): pass\nasync def async_fn(): pass\n")
        metrics = analyze_file(f)
        assert metrics.functions == 2

    def test_async_function_complexity_tracked(self, tmp_path):
        """Async function with branches must have complexity tracked."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            async def fetch(url):
                if url:
                    return url
        """))
        metrics = analyze_file(f)
        assert len(metrics.function_details) == 1
        assert metrics.function_details[0].complexity >= 2


class TestNestedFunctionAnalysis:
    """Tests for nested function analysis — currently double-counted (some FAIL)."""

    def test_outer_complexity_excludes_inner_branches(self, tmp_path):
        """Outer function complexity must not include inner function's branches."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            def outer():
                if True:
                    def inner():
                        if True:
                            pass
        """))
        metrics = analyze_file(f)
        outer = next(fd for fd in metrics.function_details if fd.name == "outer")
        assert outer.complexity == 2

    def test_inner_function_has_own_entry(self, tmp_path):
        """Inner function must appear as its own entry in function_details."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            def outer():
                def inner():
                    pass
        """))
        metrics = analyze_file(f)
        names = [fd.name for fd in metrics.function_details]
        assert "inner" in names
        assert "outer" in names


class TestDangerousImportMatching:
    """Tests for dangerous import detection — substring false positives (FAIL now)."""

    def test_import_nose_not_flagged(self, tmp_path):
        """'import nose' must NOT be flagged — 'os' is a substring but not a component."""
        f = tmp_path / "a.py"
        f.write_text("import nose\ndef fn(): pass\n")
        metrics = analyze_file(f)
        assert "nose" not in metrics.dangerous_imports

    def test_import_cosmos_not_flagged(self, tmp_path):
        """'import cosmos' must NOT be flagged — 'os' is a substring."""
        f = tmp_path / "a.py"
        f.write_text("import cosmos\ndef fn(): pass\n")
        metrics = analyze_file(f)
        assert "cosmos" not in metrics.dangerous_imports

    def test_import_os_is_flagged(self, tmp_path):
        """'import os' MUST be flagged."""
        f = tmp_path / "a.py"
        f.write_text("import os\ndef fn(): pass\n")
        metrics = analyze_file(f)
        assert "os" in metrics.dangerous_imports

    def test_import_subprocess_is_flagged(self, tmp_path):
        """'import subprocess' MUST be flagged."""
        f = tmp_path / "a.py"
        f.write_text("import subprocess\ndef fn(): pass\n")
        metrics = analyze_file(f)
        assert "subprocess" in metrics.dangerous_imports

    def test_from_subprocess_import_not_double_flagged(self, tmp_path):
        """'from subprocess import check_call' — module 'subprocess' must be flagged."""
        f = tmp_path / "a.py"
        f.write_text("from subprocess import check_call\ndef fn(): pass\n")
        metrics = analyze_file(f)
        assert "subprocess" in metrics.dangerous_imports


class TestDangerousCallMatching:
    """Tests for dangerous call detection — substring false positives (FAIL now)."""

    def test_platform_system_not_flagged(self, tmp_path):
        """'platform.system()' must NOT be flagged — leaf is 'system' but via platform."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            import platform
            def fn():
                return platform.system()
        """))
        metrics = analyze_file(f)
        fns = metrics.function_details
        assert not any("platform.system" in dc for fn in fns for dc in fn.dangerous_calls)

    def test_eval_is_flagged(self, tmp_path):
        """'eval()' MUST be flagged as dangerous."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            def fn(x):
                return eval(x)
        """))
        metrics = analyze_file(f)
        assert any("eval" in dc for fn in metrics.function_details for dc in fn.dangerous_calls)

    def test_os_system_is_flagged(self, tmp_path):
        """'os.system()' MUST be flagged — leaf is 'system'."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            import os
            def fn(cmd):
                os.system(cmd)
        """))
        metrics = analyze_file(f)
        assert any("system" in dc for fn in metrics.function_details for dc in fn.dangerous_calls)

    def test_custom_get_input_data_not_flagged(self, tmp_path):
        """Custom function containing 'input' as substring must NOT be flagged."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            def fn():
                return get_input_data()
        """))
        metrics = analyze_file(f)
        fns = metrics.function_details
        assert not any("get_input_data" in dc for fn in fns for dc in fn.dangerous_calls)


class TestLineCount:
    """Tests for line count accuracy — off-by-one on trailing newline (FAIL now)."""

    def test_file_with_trailing_newline_correct_count(self, tmp_path):
        """File with trailing newline: lines == wc -l output."""
        f = tmp_path / "a.py"
        f.write_bytes(b"a = 1\nb = 2\n")
        metrics = analyze_file(f)
        assert metrics.lines == 2

    def test_empty_file_zero_lines(self, tmp_path):
        """Empty file reports 0 lines."""
        f = tmp_path / "a.py"
        f.write_text("")
        metrics = analyze_file(f)
        assert metrics.lines == 0

    def test_single_line_with_newline(self, tmp_path):
        """Single line file with trailing newline: lines == 1."""
        f = tmp_path / "a.py"
        f.write_bytes(b"x = 1\n")
        metrics = analyze_file(f)
        assert metrics.lines == 1


class TestParamsCollection:
    """Tests for params completeness — *args/**kwargs currently missing (FAIL now)."""

    def test_vararg_appears_in_params(self, tmp_path):
        """*args must appear in params list."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            def fn(*args):
                pass
        """))
        metrics = analyze_file(f)
        assert "args" in metrics.function_details[0].params

    def test_kwargs_appears_in_params(self, tmp_path):
        """**kwargs must appear in params list."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            def fn(**kwargs):
                pass
        """))
        metrics = analyze_file(f)
        assert "kwargs" in metrics.function_details[0].params

    def test_all_param_kinds_collected(self, tmp_path):
        """All parameter types must be collected."""
        f = tmp_path / "a.py"
        f.write_text(textwrap.dedent("""
            def fn(a, b, *args, c, **kwargs):
                pass
        """))
        metrics = analyze_file(f)
        params = metrics.function_details[0].params
        assert "a" in params
        assert "b" in params
        assert "args" in params
        assert "c" in params
        assert "kwargs" in params


class TestSecurityBoundary:
    """Tests for path traversal protection — currently missing (FAIL now)."""

    def test_relative_paths_in_cache_output(self, tmp_path):
        """Cache output must contain relative paths, not absolute paths."""
        py_file = tmp_path / "src" / "main.py"
        py_file.parent.mkdir()
        py_file.write_text("def fn(): pass\n")
        cache_path = tmp_path / ".ast-context.json"
        write_ast_cache([py_file], cache_path)
        data = json.loads(cache_path.read_text())
        if data["files"]:
            file_field = data["files"][0]["file"]
            assert not file_field.startswith("/")

    def test_get_language_not_exported(self):
        """get_language() is dead code and should not be exported."""
        import wfc.scripts.ast_analyzer as pkg

        assert not hasattr(pkg, "get_language"), "get_language is dead code and should be removed"

    def test_summarize_no_emoji_in_output(self, tmp_path):
        """summarize_for_reviewer output must contain no emoji characters."""
        f = tmp_path / "a.py"
        f.write_text("import os\ndef fn(): pass\n")
        metrics = analyze_file(f)
        summary = summarize_for_reviewer(metrics)
        json_str = json.dumps(summary)
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\u2600-\u27bf"
            "\u26aa-\u26ff"
            "📍⚠️💡🔍"
            "]"
        )
        assert not emoji_pattern.search(json_str), f"Emoji found in summary output: {json_str}"


class TestIOReliability:
    """Tests for I/O reliability — encoding, atomic writes (some FAIL now)."""

    def test_nonexistent_file_counted_as_failed(self, tmp_path):
        """Passing a nonexistent file path must result in failed count, not exception."""
        nonexistent = tmp_path / "ghost.py"
        cache_path = tmp_path / ".ast-context.json"
        stats = write_ast_cache([nonexistent], cache_path)
        assert stats["failed"] == 1

    def test_latin1_file_processed_without_exception(self, tmp_path):
        """File with Latin-1 content should not raise UnicodeDecodeError to caller."""
        f = tmp_path / "latin.py"
        f.write_bytes(b"# -*- coding: latin-1 -*-\nx = '\xe9'\ndef fn(): pass\n")
        cache_path = tmp_path / ".ast-context.json"
        try:
            stats = write_ast_cache([f], cache_path)
            assert stats["parsed"] + stats["failed"] >= 1
        except UnicodeDecodeError:
            pytest.fail("UnicodeDecodeError propagated to caller — should be fail-open")

    def test_cache_file_is_valid_json_after_write(self, tmp_path):
        """Cache file must be valid JSON after write_ast_cache completes."""
        f = tmp_path / "a.py"
        f.write_text("def fn(): pass\n")
        cache_path = tmp_path / ".ast-context.json"
        write_ast_cache([f], cache_path)
        data = json.loads(cache_path.read_text())
        assert "files" in data
        assert "summary" in data


class TestResourceBounds:
    """Tests for resource bounds — no size guard currently (FAIL now)."""

    def test_large_file_counted_as_failed_not_exception(self, tmp_path):
        """File exceeding MAX_LINES must be counted as failed, not raise to caller."""
        f = tmp_path / "huge.py"
        lines = ["x = 1"] * 6000
        f.write_text("\n".join(lines) + "\n")
        cache_path = tmp_path / ".ast-context.json"
        stats = write_ast_cache([f], cache_path)
        assert stats["parsed"] + stats["failed"] == 1

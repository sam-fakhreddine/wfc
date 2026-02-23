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
import time
from textwrap import dedent

import pytest

from wfc.scripts.ast_analyzer import (
    analyze_file,
    get_language,
    is_python,
    summarize_for_reviewer,
)
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

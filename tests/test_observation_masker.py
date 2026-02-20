"""Tests for wfc.scripts.hooks.observation_masker -- context compression."""

from __future__ import annotations


class TestOutputCategory:
    def test_all_categories(self):
        from wfc.scripts.hooks.observation_masker import OutputCategory

        assert OutputCategory.FILE_CONTENT.value == "file_content"
        assert OutputCategory.TEST_RESULT.value == "test_result"
        assert OutputCategory.SEARCH_RESULT.value == "search_result"
        assert OutputCategory.COMMAND_OUTPUT.value == "command_output"
        assert OutputCategory.REASONING.value == "reasoning"
        assert OutputCategory.UNKNOWN.value == "unknown"

    def test_member_count(self):
        from wfc.scripts.hooks.observation_masker import OutputCategory

        assert len(OutputCategory) == 6


class TestCategorizeOutput:
    def test_read_tool_is_file_content(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        assert categorize_output("Read", "contents of file...").value == "file_content"

    def test_grep_tool_is_search_result(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        assert categorize_output("Grep", "match 1\nmatch 2").value == "search_result"

    def test_glob_tool_is_search_result(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        assert categorize_output("Glob", "file1.py\nfile2.py").value == "search_result"

    def test_bash_with_pytest_is_test_result(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        output = "PASSED\n5 passed in 0.5s"
        assert categorize_output("Bash", output).value == "test_result"

    def test_bash_with_test_failures_is_test_result(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        output = "FAILED tests/test_foo.py::test_bar - AssertionError"
        assert categorize_output("Bash", output).value == "test_result"

    def test_bash_generic_is_command_output(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        assert categorize_output("Bash", "some output").value == "command_output"

    def test_task_tool_is_reasoning(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        assert categorize_output("Task", "agent result...").value == "reasoning"

    def test_unknown_tool_is_unknown(self):
        from wfc.scripts.hooks.observation_masker import categorize_output

        assert categorize_output("FooTool", "data").value == "unknown"


class TestCompressOutput:
    def test_short_output_unchanged(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        short = "just a few lines"
        assert compress_output(short, "Read", threshold_chars=1000) == short

    def test_long_file_content_compressed(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        lines = [f"     {i}\tdef function_{i}(): pass" for i in range(1, 501)]
        long_output = "\n".join(lines)
        result = compress_output(long_output, "Read", threshold_chars=500)
        assert len(result) < len(long_output)
        assert "[MASKED:" in result
        assert "500 lines" in result

    def test_long_test_output_compressed(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        lines = ["PASSED test_foo.py::test_bar"] * 200
        lines.append("200 passed in 5.0s")
        long_output = "\n".join(lines)
        result = compress_output(long_output, "Bash", threshold_chars=500)
        assert len(result) < len(long_output)
        assert "[MASKED:" in result
        assert "passed" in result.lower()

    def test_preserves_error_lines(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        lines = ["ok line"] * 200
        lines.insert(50, "ERROR: something broke")
        lines.insert(100, "FAILED: test_bar")
        long_output = "\n".join(lines)
        result = compress_output(long_output, "Bash", threshold_chars=500)
        assert "ERROR: something broke" in result
        assert "FAILED: test_bar" in result

    def test_preserves_last_n_lines(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        lines = [f"line {i}" for i in range(500)]
        long_output = "\n".join(lines)
        result = compress_output(long_output, "Bash", threshold_chars=500)
        assert "line 499" in result

    def test_search_results_compressed_to_count(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        lines = [f"/path/to/file{i}.py" for i in range(200)]
        long_output = "\n".join(lines)
        result = compress_output(long_output, "Glob", threshold_chars=500)
        assert len(result) < len(long_output)
        assert "200" in result

    def test_reasoning_output_preserved(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        reasoning = "Based on analysis, the approach should be..." * 100
        result = compress_output(reasoning, "Task", threshold_chars=500)
        assert result == reasoning

    def test_empty_output_unchanged(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        assert compress_output("", "Read", threshold_chars=500) == ""

    def test_threshold_zero_always_compresses(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        result = compress_output("some output", "Read", threshold_chars=0)
        assert "[MASKED:" in result

    def test_compression_includes_category(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        long_output = "x\n" * 500
        result = compress_output(long_output, "Read", threshold_chars=100)
        assert "file_content" in result

    def test_grep_output_preserves_match_count(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        lines = [f"file{i}.py:10: match here" for i in range(200)]
        long_output = "\n".join(lines)
        result = compress_output(long_output, "Grep", threshold_chars=500)
        assert "200" in result


class TestShouldCompress:
    def test_below_threshold_no_compress(self):
        from wfc.scripts.hooks.observation_masker import should_compress

        assert should_compress(context_pct=50.0) is False

    def test_at_threshold_compress(self):
        from wfc.scripts.hooks.observation_masker import should_compress

        assert should_compress(context_pct=80.0) is True

    def test_above_threshold_compress(self):
        from wfc.scripts.hooks.observation_masker import should_compress

        assert should_compress(context_pct=95.0) is True

    def test_custom_threshold(self):
        from wfc.scripts.hooks.observation_masker import should_compress

        assert should_compress(context_pct=50.0, threshold=40.0) is True
        assert should_compress(context_pct=50.0, threshold=60.0) is False


class TestMaskSummary:
    def test_file_content_summary(self):
        from wfc.scripts.hooks.observation_masker import mask_summary

        result = mask_summary(
            tool_name="Read",
            output_lines=150,
            output_chars=5000,
            key_lines=["def main():", "class Foo:"],
        )
        assert "[MASKED: file_content" in result
        assert "150 lines" in result
        assert "def main():" in result

    def test_test_result_summary(self):
        from wfc.scripts.hooks.observation_masker import mask_summary

        result = mask_summary(
            tool_name="Bash",
            output_lines=50,
            output_chars=2000,
            key_lines=["5 passed in 1.0s"],
            is_test=True,
        )
        assert "[MASKED: test_result" in result
        assert "5 passed" in result

    def test_summary_with_errors(self):
        from wfc.scripts.hooks.observation_masker import mask_summary

        result = mask_summary(
            tool_name="Bash",
            output_lines=100,
            output_chars=3000,
            key_lines=["ERROR: module not found", "FAILED test_x"],
        )
        assert "ERROR" in result
        assert "FAILED" in result


class TestFailOpen:
    def test_compress_output_never_raises(self):
        from wfc.scripts.hooks.observation_masker import compress_output

        assert compress_output(None, "Read", threshold_chars=100) == ""
        assert compress_output(42, "Read", threshold_chars=100) == ""

    def test_categorize_output_never_raises(self):
        from wfc.scripts.hooks.observation_masker import (
            OutputCategory,
            categorize_output,
        )

        assert categorize_output(None, None) == OutputCategory.UNKNOWN
        assert categorize_output(42, 42) == OutputCategory.UNKNOWN

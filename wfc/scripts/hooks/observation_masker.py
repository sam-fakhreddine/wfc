"""PostToolUse observation masker -- context compression for WFC.

Replaces verbose tool outputs with compact summaries when context pressure
is high (>=80%). Preserves reasoning chains (Task tool output) and always
retains error/failure lines in compressed output.

Sits at the PostToolUse boundary. When context usage crosses the threshold,
file contents, test results, grep output, and command output are compressed
to structured ``[MASKED: ...]`` summaries while keeping the information
needed for continued reasoning.

Design principles:
  - Fail-open: every public function catches exceptions and returns a safe
    default so that masking failures never block the agent.
  - REASONING is never compressed (preserve the chain).
  - Error/failure lines are always preserved in compressed output.
  - ``[MASKED: category, N lines, M chars]`` format for compressed blocks.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List


class OutputCategory(Enum):
    """Categories of tool output for compression decisions."""

    FILE_CONTENT = "file_content"
    TEST_RESULT = "test_result"
    SEARCH_RESULT = "search_result"
    COMMAND_OUTPUT = "command_output"
    REASONING = "reasoning"
    UNKNOWN = "unknown"


_TEST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bPASSED\b"),
    re.compile(r"\bFAILED\b"),
    re.compile(r"\d+\s+passed"),
    re.compile(r"\d+\s+failed"),
    re.compile(r"\bpytest\b", re.IGNORECASE),
    re.compile(r"\btest_\w+", re.IGNORECASE),
]

_ERROR_LINE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^ERROR\b", re.IGNORECASE),
    re.compile(r"^FAILED\b", re.IGNORECASE),
    re.compile(r"^WARN(?:ING)?\b", re.IGNORECASE),
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"^\s*raise\s+\w+"),
    re.compile(r"AssertionError|AssertionError|AssertionError"),
    re.compile(r"Exception:|Error:"),
]

_DEFINITION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*(?:def|class|async def)\s+\w+"),
    re.compile(r"^\s*(?:function|const|let|var|export)\s+\w+"),
    re.compile(r"^\s*(?:func|type|struct|impl)\s+\w+"),
]

_TEST_SUMMARY_PATTERN = re.compile(
    r"\d+\s+(?:passed|failed|error|skipped|warning).*(?:in\s+[\d.]+s)?",
    re.IGNORECASE,
)


def categorize_output(tool_name: object, output: object) -> OutputCategory:
    """Map a tool name + output content to an OutputCategory.

    Fail-open: returns UNKNOWN on any exception or unexpected input.
    """
    try:
        tool = str(tool_name) if tool_name is not None else ""
        text = str(output) if output is not None else ""

        if tool == "Read":
            return OutputCategory.FILE_CONTENT
        if tool in ("Grep", "Glob"):
            return OutputCategory.SEARCH_RESULT
        if tool == "Task":
            return OutputCategory.REASONING

        if tool == "Bash":
            for pat in _TEST_PATTERNS:
                if pat.search(text):
                    return OutputCategory.TEST_RESULT
            return OutputCategory.COMMAND_OUTPUT

        return OutputCategory.UNKNOWN
    except Exception:
        return OutputCategory.UNKNOWN


def should_compress(context_pct: float, threshold: float = 80.0) -> bool:
    """Return True if context pressure warrants compression."""
    try:
        return float(context_pct) >= float(threshold)
    except (TypeError, ValueError):
        return False


def _extract_key_lines(lines: list[str], category: OutputCategory) -> list[str]:
    """Extract the most important lines from *lines* for a given category."""
    key: list[str] = []

    for line in lines:
        for pat in _ERROR_LINE_PATTERNS:
            if pat.search(line):
                key.append(line)
                break

    if category == OutputCategory.FILE_CONTENT:
        for line in lines:
            for pat in _DEFINITION_PATTERNS:
                if pat.search(line):
                    key.append(line)
                    break

    elif category == OutputCategory.TEST_RESULT:
        for line in lines:
            if _TEST_SUMMARY_PATTERN.search(line):
                key.append(line)

    elif category == OutputCategory.SEARCH_RESULT:
        if len(lines) > 6:
            key.extend(lines[:3])
            key.extend(lines[-3:])
        else:
            key.extend(lines)

    tail = lines[-5:] if len(lines) >= 5 else lines[:]
    for t in tail:
        if t not in key:
            key.append(t)

    return key


def mask_summary(
    tool_name: str,
    output_lines: int,
    output_chars: int,
    key_lines: List[str],
    is_test: bool = False,
) -> str:
    """Build a ``[MASKED: ...]`` summary block.

    Parameters
    ----------
    tool_name:
        Name of the originating tool (used for category detection).
    output_lines:
        Number of lines in the original output.
    output_chars:
        Number of characters in the original output.
    key_lines:
        Important lines extracted from the original output.
    is_test:
        If True, forces category to TEST_RESULT.
    """
    try:
        if is_test:
            category = OutputCategory.TEST_RESULT
        else:
            category = categorize_output(tool_name, "\n".join(key_lines))

        header = f"[MASKED: {category.value}, {output_lines} lines, {output_chars} chars]"

        if key_lines:
            body = "\n".join(key_lines)
            return f"{header}\n{body}"
        return header
    except Exception:
        return f"[MASKED: unknown, {output_lines} lines, {output_chars} chars]"


def compress_output(
    output: object,
    tool_name: str,
    threshold_chars: int = 2000,
) -> str:
    """Compress *output* if it exceeds *threshold_chars*.

    Returns the original output unchanged when:
      - it is shorter than *threshold_chars*
      - the category is REASONING (preserve the chain)
      - *output* is empty

    Otherwise builds a ``[MASKED: ...]`` summary preserving key lines
    (errors, definitions, test summaries, tail).

    Fail-open: on any exception returns the original string (or ``""``).
    """
    try:
        if output is None or not isinstance(output, str):
            return ""

        if not output:
            return ""

        category = categorize_output(tool_name, output)

        if category == OutputCategory.REASONING:
            return output

        if len(output) <= threshold_chars:
            return output

        lines = output.split("\n")
        line_count = len(lines)

        key_lines = _extract_key_lines(lines, category)

        is_test = category == OutputCategory.TEST_RESULT

        if category == OutputCategory.SEARCH_RESULT:
            count_line = f"({line_count} results total)"
            key_lines.insert(0, count_line)

        return mask_summary(
            tool_name=tool_name,
            output_lines=line_count,
            output_chars=len(output),
            key_lines=key_lines,
            is_test=is_test,
        )
    except Exception:
        if isinstance(output, str):
            return output
        return ""

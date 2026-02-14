"""Python quality checker — auto-format with ruff, lint, type check."""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _util import GREEN, NC, RED, check_file_length


def strip_python_comments(file_path: Path) -> bool:
    """Remove inline comments from Python file using tokenizer.

    Preserves: shebangs, type hints, noqa, pragma, linter directives,
    TODO/FIXME/XXX/NOTE markers.
    """
    try:
        content = file_path.read_text()
    except Exception:
        return False

    preserve_patterns = [
        r"#!",
        r"#\s*type:",
        r"#\s*noqa",
        r"#\s*pragma:",
        r"#\s*pylint:",
        r"#\s*pyright:",
        r"#\s*ruff:",
        r"#\s*fmt:",
        r"#\s*TODO",
        r"#\s*FIXME",
        r"#\s*XXX",
        r"#\s*NOTE",
    ]
    preserve_re = re.compile("|".join(preserve_patterns), re.IGNORECASE)

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
    except tokenize.TokenError:
        return False

    lines = content.splitlines(keepends=True)
    comments_to_remove: list[tuple[int, int, int]] = []

    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            if preserve_re.search(tok.string):
                continue
            start_row, start_col = tok.start
            _, end_col = tok.end
            comments_to_remove.append((start_row, start_col, end_col))

    if not comments_to_remove:
        return False

    new_lines = list(lines)
    lines_to_delete: set[int] = set()

    for line_num, start_col, _ in reversed(comments_to_remove):
        idx = line_num - 1
        if idx >= len(new_lines):
            continue
        line = new_lines[idx]
        before_comment = line[:start_col].rstrip()
        if before_comment:
            new_lines[idx] = before_comment + "\n"
        else:
            lines_to_delete.add(idx)

    for idx in sorted(lines_to_delete, reverse=True):
        del new_lines[idx]

    new_content = "".join(new_lines)
    if new_content != content:
        file_path.write_text(new_content)
        return True
    return False


def check_python(file_path: Path) -> tuple[int, str]:
    """Check Python file: strip comments, auto-format, lint, type-check.

    Returns (exit_code, reason).
    """
    strip_python_comments(file_path)

    if "test_" in file_path.name or "spec" in file_path.name:
        return 0, ""

    check_file_length(file_path)

    ruff_bin = shutil.which("ruff")
    if ruff_bin:
        try:
            subprocess.run(
                [ruff_bin, "check", "--select", "I,RUF022", "--fix", str(file_path)],
                capture_output=True,
                check=False,
            )
            subprocess.run(
                [ruff_bin, "format", str(file_path)],
                capture_output=True,
                check=False,
            )
        except Exception:
            pass

    has_ruff = ruff_bin is not None
    has_pyright = shutil.which("basedpyright") is not None or shutil.which("pyright") is not None

    if not (has_ruff or has_pyright):
        return 0, ""

    results: dict[str, tuple] = {}
    has_issues = False

    if has_ruff and ruff_bin:
        try:
            result = subprocess.run(
                [ruff_bin, "check", "--output-format=concise", str(file_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout + result.stderr
            error_pattern = re.compile(r":\d+:\d+: [A-Z]{1,3}\d+")
            error_lines = [
                line for line in output.splitlines() if error_pattern.search(line)
            ]
            if error_lines:
                has_issues = True
                results["ruff"] = (len(error_lines), error_lines)
        except Exception:
            pass

    pyright_bin = shutil.which("basedpyright") or shutil.which("pyright")
    if pyright_bin:
        try:
            result = subprocess.run(
                [pyright_bin, "--outputjson", str(file_path.resolve())],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout + result.stderr
            try:
                data = json.loads(output)
                error_count = data.get("summary", {}).get("errorCount", 0)
                if error_count > 0:
                    has_issues = True
                    results["pyright"] = (
                        error_count,
                        data.get("generalDiagnostics", []),
                    )
            except json.JSONDecodeError:
                pass
        except Exception:
            pass

    if has_issues:
        _print_python_issues(file_path, results)
        parts = []
        for tool_name, (count, _) in results.items():
            parts.append(f"{count} {tool_name}")
        reason = f"Python: {', '.join(parts)} in {file_path.name}"
        return 2, reason

    print("", file=sys.stderr)
    print(f"{GREEN}Python: All checks passed{NC}", file=sys.stderr)
    return 2, ""


def _print_python_issues(file_path: Path, results: dict[str, tuple]) -> None:
    """Print Python diagnostic issues to stderr."""
    print("", file=sys.stderr)
    try:
        display_path = file_path.relative_to(Path.cwd())
    except ValueError:
        display_path = file_path
    print(f"{RED}Python issues in: {display_path}{NC}", file=sys.stderr)

    if "ruff" in results:
        count, error_lines = results["ruff"]
        plural = "issue" if count == 1 else "issues"
        print("", file=sys.stderr)
        print(f"  Ruff: {count} {plural}", file=sys.stderr)
        print("  " + "-" * 38, file=sys.stderr)
        for line in error_lines[:10]:
            parts = line.split(None, 1)
            if parts:
                code = parts[0]
                msg = parts[1] if len(parts) > 1 else ""
                msg = msg.replace("[*] ", "")
                print(f"    {code}: {msg}", file=sys.stderr)
        if count > 10:
            print(f"    ... and {count - 10} more", file=sys.stderr)
        print("", file=sys.stderr)

    if "pyright" in results:
        count, diagnostics = results["pyright"]
        plural = "issue" if count == 1 else "issues"
        print("", file=sys.stderr)
        print(f"  Pyright: {count} {plural}", file=sys.stderr)
        print("  " + "-" * 38, file=sys.stderr)
        for diag in diagnostics[:10]:
            file_name = Path(diag.get("file", "")).name
            line = diag.get("range", {}).get("start", {}).get("line", 0)
            msg = diag.get("message", "").split("\n")[0]
            print(f"    {file_name}:{line} - {msg}", file=sys.stderr)
        if count > 10:
            print(f"    ... and {count - 10} more", file=sys.stderr)
        print("", file=sys.stderr)

    print(f"{RED}Fix Python issues above before continuing{NC}", file=sys.stderr)

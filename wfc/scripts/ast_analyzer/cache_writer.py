"""
AST cache writer for shared reviewer context.

Analyzes changed files (via git diff), extracts AST metrics for Python files only,
and writes results to `.wfc-review/.ast-context.json` for reviewer consumption.

Fail-open strategy: Parse failures are logged but don't block the review.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

from .language_detection import is_python
from .metrics_extractor import analyze_file, summarize_for_reviewer


def write_ast_cache(
    changed_files: List[Path], output_path: Path, exclude_dirs: List[str] | None = None
) -> Dict:
    """
    Analyze changed Python files and write AST metrics to cache file.

    Args:
        changed_files: List of files to analyze (from git diff)
        output_path: Path to write .ast-context.json
        exclude_dirs: Directories to exclude (default: .worktrees, .venv, __pycache__)

    Returns:
        Summary dict with parse statistics:
        {
            "parsed": N,
            "failed": M,
            "duration_ms": X
        }

    Note:
        Fail-open: Parse failures are logged to stderr but don't raise exceptions.
        The cache file is written even if some files fail to parse.
    """
    if exclude_dirs is None:
        exclude_dirs = [".worktrees", ".venv", "__pycache__", ".git", "node_modules"]

    start_time = time.perf_counter()
    parsed_count = 0
    failed_count = 0
    file_summaries = []

    for file_path in changed_files:
        try:
            file_path = file_path.resolve()
        except OSError:
            failed_count += 1
            continue

        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue

        if not is_python(file_path):
            continue

        try:
            metrics = analyze_file(file_path)
            summary = summarize_for_reviewer(metrics)
            file_summaries.append(summary)
            parsed_count += 1
        except SyntaxError as e:
            print(
                f"⚠️  AST parse failed for {file_path}: {e}",
                file=sys.stderr,
            )
            failed_count += 1
        except Exception as e:
            print(
                f"⚠️  AST analysis failed for {file_path}: {e}",
                file=sys.stderr,
            )
            failed_count += 1

    duration_ms = (time.perf_counter() - start_time) * 1000

    cache_data = {
        "files": file_summaries,
        "summary": {
            "total_files": len(changed_files),
            "parsed": parsed_count,
            "failed": failed_count,
            "duration_ms": round(duration_ms, 2),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(cache_data))
        os.replace(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    return cache_data["summary"]

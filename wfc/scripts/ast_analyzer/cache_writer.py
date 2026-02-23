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
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from pathlib import Path

from .language_detection import is_python
from .metrics_extractor import analyze_file, summarize_for_reviewer

_BATCH_TIMEOUT = 30.0  # seconds for entire batch


def _analyze_and_summarize(file_path: Path) -> dict:
    """Analyze a single Python file and return its summary. Raises on error."""
    metrics = analyze_file(file_path)
    return summarize_for_reviewer(metrics)


def _build_cache_data(python_files: list[Path], changed_files_count: int) -> dict:
    """Build cache data dict from Python files. Pure function with no I/O except file reading."""
    parsed_count = 0
    failed_count = 0
    file_summaries = []

    max_workers = min(8, len(python_files) or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_analyze_and_summarize, fp): fp for fp in python_files}
        try:
            for future in as_completed(futures, timeout=_BATCH_TIMEOUT):
                fp = futures[future]
                try:
                    # future.result() has no timeout here — as_completed only yields completed futures.
                    # Per-file wall-clock limit is enforced by the _BATCH_TIMEOUT on as_completed().
                    summary = future.result()
                    file_summaries.append(summary)
                    parsed_count += 1
                except SyntaxError as e:
                    print(f"AST parse failed for {fp}: {e}", file=sys.stderr)
                    failed_count += 1
                except Exception as e:
                    print(f"AST analysis failed for {fp}: {e}", file=sys.stderr)
                    failed_count += 1
        except TimeoutError:
            for future, fp in futures.items():
                if future.done():
                    try:
                        summary = future.result()
                        file_summaries.append(summary)
                        parsed_count += 1
                    except Exception as e:
                        print(f"AST analysis failed for {fp}: {e}", file=sys.stderr)
                        failed_count += 1
                else:
                    future.cancel()
                    print(f"AST analysis batch timeout, skipping {fp}", file=sys.stderr)
                    failed_count += 1

    return {
        "files": file_summaries,
        "summary": {
            "total_files": changed_files_count,
            "parsed": parsed_count,
            "failed": failed_count,
        },
    }


def write_ast_cache(
    changed_files: list[Path], output_path: Path, exclude_dirs: list[str] | None = None
) -> dict:
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

    # Filter to Python files within project bounds
    failed_count = 0
    python_files = []
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
        python_files.append(file_path)

    start_time = time.perf_counter()
    cache_data = _build_cache_data(python_files, len(changed_files))
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Incorporate any pre-filter failures into the summary
    cache_data["summary"]["failed"] += failed_count
    cache_data["summary"]["duration_ms"] = round(duration_ms, 2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(cache_data))
        os.replace(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            print(f"DEBUG: AST cache tmp file cleanup: {tmp_path}", file=sys.stderr)
            tmp_path.unlink(missing_ok=True)

    return cache_data["summary"]

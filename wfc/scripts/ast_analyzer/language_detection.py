"""
Language detection for AST analyzer.

Currently supports Python-only. Extensible for future multi-language support.
"""

from pathlib import Path


def is_python(file_path: Path) -> bool:
    """
    Check if a file is a Python source file.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file is a Python source file, False otherwise

    Examples:
        >>> is_python(Path("script.py"))
        True
        >>> is_python(Path("README.md"))
        False
    """
    return file_path.suffix == ".py"

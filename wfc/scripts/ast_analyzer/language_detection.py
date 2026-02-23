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


def get_language(file_path: Path) -> str:
    """
    Detect the programming language of a file.

    Args:
        file_path: Path to the file

    Returns:
        Language identifier ("python", "unknown")

    Note:
        Currently only supports Python. Future versions will add:
        - JavaScript/TypeScript (.js, .jsx, .ts, .tsx)
        - Go (.go)
        - Rust (.rs)
        - Java (.java)

    Deprecated:
        This function is not exported from the package. Use is_python() instead.
    """
    if is_python(file_path):
        return "python"
    return "unknown"

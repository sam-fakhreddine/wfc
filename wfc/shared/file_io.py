"""
WFC File I/O Utilities

Safe, consistent file operations with proper error handling.
Eliminates inline boilerplate for JSON, YAML, and text file operations.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from filelock import FileLock, Timeout


class FileIOError(Exception):
    """Base exception for file I/O errors"""

    pass


def load_json(path: Path, default: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Load JSON file safely with proper error handling.

    Args:
        path: Path to JSON file
        default: Default value if file doesn't exist (returns this instead of error)

    Returns:
        Parsed JSON as dict

    Raises:
        FileIOError: If file exists but can't be read or parsed

    Example:
        config = load_json(Path('config.json'))
        config = load_json(Path('config.json'), default={})  # Returns {} if missing
    """
    try:
        if not Path(path).exists():
            if default is not None:
                return default
            raise FileIOError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        raise FileIOError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        raise FileIOError(f"Error reading {path}: {e}")


def save_json(
    path: Path, data: Dict[str, Any], indent: int = 2, ensure_parent: bool = True
) -> None:
    """
    Save JSON file safely with proper formatting.

    Args:
        path: Path to save JSON file
        data: Dict to save as JSON
        indent: JSON indentation (default: 2 spaces)
        ensure_parent: Create parent directory if needed (default: True)

    Raises:
        FileIOError: If file can't be written

    Example:
        save_json(Path('config.json'), {'key': 'value'})
        save_json(Path('data.json'), data, indent=4)
    """
    try:
        path = Path(path)

        if ensure_parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    except Exception as e:
        raise FileIOError(f"Error writing {path}: {e}")


def update_json(
    path: Path, updates: Dict[str, Any], create_if_missing: bool = True
) -> Dict[str, Any]:
    """
    Update JSON file with new values (merge operation).

    Args:
        path: Path to JSON file
        updates: Dict with values to update
        create_if_missing: Create file if doesn't exist (default: True)

    Returns:
        Updated dict (after merge)

    Raises:
        FileIOError: If file can't be read or written

    Example:
        # Update existing config
        config = update_json(Path('config.json'), {'new_key': 'value'})

        # Merge deeply
        config = update_json(Path('config.json'), {'nested': {'key': 'value'}})
    """
    try:
        if Path(path).exists():
            data = load_json(path)
        elif create_if_missing:
            data = {}
        else:
            raise FileIOError(f"File not found and create_if_missing=False: {path}")

        data.update(updates)

        save_json(path, data)

        return data

    except FileIOError:
        raise
    except Exception as e:
        raise FileIOError(f"Error updating {path}: {e}")


def load_text(path: Path, default: Optional[str] = None) -> str:
    """
    Load text file safely.

    Args:
        path: Path to text file
        default: Default value if file doesn't exist

    Returns:
        File contents as string

    Raises:
        FileIOError: If file exists but can't be read

    Example:
        content = load_text(Path('README.md'))
        content = load_text(Path('notes.txt'), default='')
    """
    try:
        if not Path(path).exists():
            if default is not None:
                return default
            raise FileIOError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        raise FileIOError(f"Error reading {path}: {e}")


def save_text(path: Path, content: str, ensure_parent: bool = True) -> None:
    """
    Save text file safely.

    Args:
        path: Path to save text file
        content: String content to save
        ensure_parent: Create parent directory if needed (default: True)

    Raises:
        FileIOError: If file can't be written

    Example:
        save_text(Path('README.md'), '# My Project')
    """
    try:
        path = Path(path)

        if ensure_parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    except Exception as e:
        raise FileIOError(f"Error writing {path}: {e}")


def safe_append_text(
    path: Path, content: str, ensure_parent: bool = True, timeout: int = 10
) -> None:
    """
    Append to text file safely with file locking for concurrent writes.

    Args:
        path: Path to text file
        content: String content to append
        ensure_parent: Create parent directory if needed (default: True)
        timeout: Lock timeout in seconds (default: 10)

    Raises:
        FileIOError: If file can't be written or lock times out

    Example:
        safe_append_text(Path('log.txt'), 'New log entry\\n')
        safe_append_text(Path('log.txt'), 'Entry\\n', timeout=5)
    """
    try:
        path = Path(path).resolve()
        lock_path = path.parent / f"{path.name}.lock"
        lock_path = lock_path.resolve()

        if lock_path.parent != path.parent:
            raise FileIOError(f"Lock file path traversal detected: {lock_path}")

        if ensure_parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with FileLock(lock_path, timeout=timeout):
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

    except Timeout:
        raise FileIOError(f"Failed to acquire lock for {path} within {timeout}s")
    except FileIOError:
        raise
    except Exception as e:
        raise FileIOError(f"Error appending to {path}: {e}")


def append_text(path: Path, content: str, ensure_parent: bool = True) -> None:
    """
    Append to text file safely (delegates to safe_append_text).

    Args:
        path: Path to text file
        content: String content to append
        ensure_parent: Create parent directory if needed (default: True)

    Raises:
        FileIOError: If file can't be written

    Example:
        append_text(Path('log.txt'), 'New log entry\\n')
    """
    safe_append_text(path, content, ensure_parent=ensure_parent)


read_json = load_json
write_json = save_json
read_text = load_text
write_text = save_text


if __name__ == "__main__":
    import shutil
    import tempfile

    temp_dir = Path(tempfile.mkdtemp())

    try:
        print("Testing WFC File I/O Utilities\n")

        print("1. Testing JSON operations:")
        test_data = {"name": "WFC", "version": "1.0", "features": ["build", "review"]}
        json_file = temp_dir / "test.json"

        save_json(json_file, test_data)
        print(f"   ✅ Saved JSON to {json_file}")

        loaded = load_json(json_file)
        assert loaded == test_data
        print(f"   ✅ Loaded JSON: {loaded}")

        print("\n2. Testing JSON update:")
        updated = update_json(json_file, {"new_key": "new_value"})
        print(f"   ✅ Updated JSON: {updated}")

        print("\n3. Testing default values:")
        missing = load_json(temp_dir / "missing.json", default={"default": True})
        print(f"   ✅ Missing file returned default: {missing}")

        print("\n4. Testing text operations:")
        text_file = temp_dir / "test.txt"
        save_text(text_file, "Hello WFC\n")
        print("   ✅ Saved text")

        append_text(text_file, "Second line\n")
        print("   ✅ Appended text")

        content = load_text(text_file)
        assert content == "Hello WFC\nSecond line\n"
        print(f"   ✅ Loaded text: {repr(content)}")

        print("\n5. Testing error handling:")
        try:
            load_json(temp_dir / "missing.json")
            print("   ❌ Should have raised error")
        except FileIOError as e:
            print(f"   ✅ Correctly raised error: {e}")

        print("\n✅ All tests passed!")

    finally:
        shutil.rmtree(temp_dir)
        print("\n🧹 Cleaned up temp directory")

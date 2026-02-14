#!/usr/bin/env python3
"""PostToolUse file checker — dispatches to language-specific quality checkers.

Called after every Write/Edit tool use. Reads the edited file path from
stdin (Claude Code hook protocol), then runs the appropriate language
checker: Python (ruff), TypeScript (eslint/prettier/tsc), Go (gofmt/vet).

Each checker:
  1. Strips inline comments (preserving directives)
  2. Auto-formats the file
  3. Runs linting and type checking
  4. Reports issues as non-blocking warnings (exit code 2)

Exit codes:
  0 = no issues or unsupported language
  2 = issues found (non-blocking notification to Claude)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _checkers.go import check_go
from _checkers.python import check_python
from _checkers.typescript import TS_EXTENSIONS, check_typescript
from _util import find_git_root, get_edited_file_from_stdin


def main() -> int:
    """Main entry point — dispatch by file extension."""
    try:
        return _run()
    except Exception:
        return 0


def _run() -> int:
    git_root = find_git_root()
    if git_root:
        os.chdir(git_root)

    target_file = get_edited_file_from_stdin()
    if not target_file or not target_file.exists():
        return 0

    if target_file.suffix == ".py":
        exit_code, reason = check_python(target_file)
    elif target_file.suffix in TS_EXTENSIONS:
        exit_code, reason = check_typescript(target_file)
    elif target_file.suffix == ".go":
        exit_code, reason = check_go(target_file)
    else:
        return 0

    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))
    else:
        print(json.dumps({}))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

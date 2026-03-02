#!/usr/bin/env python3
"""PostToolUse hook: record skill name on every Skill tool call."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name != "Skill":
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    skill = tool_input.get("skill", "unknown")
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

    log_dir = Path.home() / ".claude" / "usage-data" / "skill-invocations"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{session_id}.jsonl"

    entry = {
        "session_id": session_id,
        "skill": skill,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    main()

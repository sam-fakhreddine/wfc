"""DocumentationAgent — CRUD documentation agent with exclusive write permissions.

Provides a formal payload schema (DocumentationCRUDPayload) and agent that
mediates all documentation writes. Every operation is validated, executed,
and emitted to the observability bus.

Design principles:
  - Fail-open: errors are caught and returned in the result dict, never raised.
  - Security: paths are validated against ALLOWED_PREFIXES; traversal and
    absolute paths are rejected.
  - Observability: every execute() call emits a structured event via
    _emit_doc_event(). If emission fails, the operation still succeeds.
  - Zero new dependencies: pure stdlib only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any

logger = logging.getLogger(__name__)


ALLOWED_PREFIXES: tuple[str, ...] = (
    "docs/",
    "docs/solutions/",
)


class DocumentationAction(Enum):
    """Supported CRUD actions for documentation payloads."""

    CREATE = "create"
    UPDATE = "update"
    APPEND = "append"
    DELETE = "delete"


_VALID_ACTIONS = {a.value for a in DocumentationAction}

_REQUIRED_FIELDS = ("action", "target_file", "rationale")


def validate_payload(raw: Any) -> dict[str, Any] | None:
    """Validate and normalize a documentation CRUD payload.

    Returns a normalized dict on success, or None on validation failure.

    Required fields:
      - action: one of "create", "update", "append", "delete"
      - target_file: relative path starting with an allowed prefix
      - rationale: human-readable reason for the change

    Optional fields (defaults applied):
      - content: str (default "")
      - generating_agent: str (default "unknown")
      - workflow_id: str (default "")

    Security:
      - Absolute paths are rejected.
      - Path traversal (.. components) is rejected.
      - Paths not starting with an allowed prefix are rejected.
    """
    if not isinstance(raw, dict):
        return None

    for field in _REQUIRED_FIELDS:
        if field not in raw:
            return None

    action = raw["action"]
    if action not in _VALID_ACTIONS:
        return None

    target_file = raw["target_file"]
    if not isinstance(target_file, str):
        return None

    # Security: reject absolute paths
    if target_file.startswith("/"):
        return None

    # Security: reject path traversal
    posix = PurePosixPath(target_file)
    if ".." in posix.parts:
        return None

    # Security: must start with an allowed prefix
    if not any(target_file.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return None

    rationale = str(raw["rationale"]).strip()
    if not rationale:
        return None

    return {
        "action": action,
        "target_file": target_file,
        "content": str(raw.get("content", "")),
        "rationale": rationale,
        "generating_agent": str(raw.get("generating_agent", "unknown")),
        "workflow_id": str(raw.get("workflow_id", "")),
    }


def _emit_doc_event(result: dict[str, Any]) -> None:
    """Emit a structured documentation event to the observability bus.

    This function MUST never raise. If emission fails, the error is logged
    and silently swallowed so that the calling operation still succeeds.
    """
    try:
        logger.info(
            "doc_event: action=%s target=%s success=%s agent=%s",
            result.get("action", "?"),
            result.get("target_file", "?"),
            result.get("success", "?"),
            result.get("generating_agent", "?"),
        )
    except Exception:  # noqa: BLE001
        pass


class DocumentationAgent:
    """Agent with exclusive write permissions for documentation files.

    All documentation mutations (create, update, append, delete) must go
    through this agent. It validates payloads, executes the filesystem
    operation, and emits an observability event.

    Args:
        base_dir: Project root directory. All target_file paths are resolved
                  relative to this directory.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = Path(base_dir)

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate and execute a documentation CRUD payload.

        Returns a result dict with at minimum:
          - success: bool
          - timestamp: ISO-8601 string
          - action: str (if payload was valid)
          - target_file: str (if payload was valid)
          - generating_agent: str (if payload was valid)
          - error: str (if success is False)
        """
        timestamp = datetime.now(tz=timezone.utc).isoformat()

        validated = validate_payload(payload)
        if validated is None:
            result: dict[str, Any] = {
                "success": False,
                "error": "Invalid payload: validation failed",
                "timestamp": timestamp,
            }
            try:
                _emit_doc_event(result)
            except Exception:  # noqa: BLE001
                pass
            return result

        action = validated["action"]
        target_file = validated["target_file"]
        content = validated["content"]
        generating_agent = validated["generating_agent"]

        full_path = self._base_dir / target_file

        try:
            if action == DocumentationAction.CREATE.value:
                result = self._do_create(full_path, content)
            elif action == DocumentationAction.UPDATE.value:
                result = self._do_update(full_path, content)
            elif action == DocumentationAction.APPEND.value:
                result = self._do_append(full_path, content)
            elif action == DocumentationAction.DELETE.value:
                result = self._do_delete(full_path)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
        except Exception as exc:  # noqa: BLE001
            result = {"success": False, "error": str(exc)}

        result["action"] = action
        result["target_file"] = target_file
        result["generating_agent"] = generating_agent
        result["timestamp"] = timestamp

        try:
            _emit_doc_event(result)
        except Exception:  # noqa: BLE001
            pass

        return result

    @staticmethod
    def _do_create(path: Path, content: str) -> dict[str, Any]:
        """Create a new documentation file. Refuses if file already exists."""
        if path.exists():
            return {
                "success": False,
                "error": f"File already exists: {path.name}",
            }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return {"success": True}

    @staticmethod
    def _do_update(path: Path, content: str) -> dict[str, Any]:
        """Overwrite an existing documentation file. Refuses if not found."""
        if not path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {path.name}",
            }
        path.write_text(content)
        return {"success": True}

    @staticmethod
    def _do_append(path: Path, content: str) -> dict[str, Any]:
        """Append content to an existing documentation file. Refuses if not found."""
        if not path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {path.name}",
            }
        existing = path.read_text()
        path.write_text(existing + content)
        return {"success": True}

    @staticmethod
    def _do_delete(path: Path) -> dict[str, Any]:
        """Delete a documentation file. Refuses if not found."""
        if not path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {path.name}",
            }
        path.unlink()
        return {"success": True}

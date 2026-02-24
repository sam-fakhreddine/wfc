"""
API key authentication for WFC REST API.

File-based storage at ~/.wfc/api_keys.json with filelock protection.
"""

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from filelock import FileLock


class APIKeyStore:
    """
    File-based API key storage.

    Format: ~/.wfc/api_keys.json
    {
        "project1": {
            "api_key_hash": "sha256...",
            "developer_id": "alice",
            "created_at": "2026-02-21T14:00:00Z"
        }
    }
    """

    def __init__(self, store_path: Optional[Path] = None):
        """Initialize API key store."""
        self.store_path = store_path or (Path.home() / ".wfc" / "api_keys.json")
        self.lock_path = self.store_path.with_suffix(".json.lock")

        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.store_path.exists():
            self._write_store({})

    def generate_api_key(self) -> str:
        """Generate cryptographically secure API key."""
        return secrets.token_urlsafe(32)

    def hash_api_key(self, api_key: str) -> str:
        """Hash API key using SHA-256."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_api_key(self, project_id: str, developer_id: str) -> str:
        """
        Create new API key for project.

        Args:
            project_id: Project identifier
            developer_id: Developer identifier

        Returns:
            Generated API key (plaintext, return to user)

        Raises:
            ValueError: If project already has API key
        """
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()

            if project_id in store:
                raise ValueError(f"Project {project_id} already has API key")

            api_key = self.generate_api_key()
            api_key_hash = self.hash_api_key(api_key)

            store[project_id] = {
                "api_key_hash": api_key_hash,
                "developer_id": developer_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            self._write_store(store)

            return api_key

    def validate_api_key(self, project_id: str, api_key: str) -> bool:
        """
        Validate API key for project.

        Args:
            project_id: Project identifier
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()

            if project_id not in store:
                return False

            expected_hash = store[project_id]["api_key_hash"]
            actual_hash = self.hash_api_key(api_key)

            return secrets.compare_digest(expected_hash, actual_hash)

    def get_developer_id(self, project_id: str) -> Optional[str]:
        """Get developer_id for project."""
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()
            return store.get(project_id, {}).get("developer_id")

    def list_projects(self) -> Dict[str, dict]:
        """List all projects."""
        with FileLock(self.lock_path, timeout=10):
            return self._read_store()

    def revoke_api_key(self, project_id: str) -> None:
        """Revoke API key for project."""
        with FileLock(self.lock_path, timeout=10):
            store = self._read_store()
            if project_id in store:
                del store[project_id]
                self._write_store(store)

    def _read_store(self) -> Dict[str, dict]:
        """Read API key store from disk."""
        if not self.store_path.exists():
            return {}

        with open(self.store_path, "r") as f:
            return json.load(f)

    def _write_store(self, store: Dict[str, dict]) -> None:
        """Write API key store to disk."""
        with open(self.store_path, "w") as f:
            json.dump(store, f, indent=2)

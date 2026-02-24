"""
Unit tests for API key authentication.

TDD RED phase: these tests define expected behavior for auth.py
"""

import json

import pytest

from wfc.servers.rest_api.auth import APIKeyStore


class TestAPIKeyStore:
    """Test APIKeyStore functionality."""

    @pytest.fixture
    def tmp_store(self, tmp_path):
        """Create temporary API key store."""
        store_path = tmp_path / "api_keys.json"
        return APIKeyStore(store_path=store_path)

    def test_create_api_key_generates_unique_key(self, tmp_store):
        """Each API key should be unique."""
        key1 = tmp_store.create_api_key("proj1", "alice")
        key2 = tmp_store.create_api_key("proj2", "bob")

        assert key1 != key2
        assert len(key1) > 30

    def test_validate_api_key_accepts_valid_key(self, tmp_store):
        """Valid API key should be accepted."""
        api_key = tmp_store.create_api_key("proj1", "alice")

        assert tmp_store.validate_api_key("proj1", api_key) is True

    def test_validate_api_key_rejects_invalid_key(self, tmp_store):
        """Invalid API key should be rejected."""
        tmp_store.create_api_key("proj1", "alice")

        assert tmp_store.validate_api_key("proj1", "wrong-key") is False

    def test_validate_api_key_rejects_nonexistent_project(self, tmp_store):
        """Non-existent project should be rejected."""
        assert tmp_store.validate_api_key("nonexistent", "any-key") is False

    def test_create_duplicate_project_fails(self, tmp_store):
        """Creating duplicate project should raise ValueError."""
        tmp_store.create_api_key("proj1", "alice")

        with pytest.raises(ValueError, match="already has API key"):
            tmp_store.create_api_key("proj1", "bob")

    def test_get_developer_id_returns_correct_id(self, tmp_store):
        """get_developer_id should return correct developer."""
        tmp_store.create_api_key("proj1", "alice")

        assert tmp_store.get_developer_id("proj1") == "alice"

    def test_get_developer_id_nonexistent_project(self, tmp_store):
        """get_developer_id for non-existent project should return None."""
        assert tmp_store.get_developer_id("nonexistent") is None

    def test_revoke_api_key_invalidates_key(self, tmp_store):
        """Revoked API key should no longer validate."""
        api_key = tmp_store.create_api_key("proj1", "alice")

        tmp_store.revoke_api_key("proj1")

        assert tmp_store.validate_api_key("proj1", api_key) is False

    def test_revoke_nonexistent_project_no_error(self, tmp_store):
        """Revoking non-existent project should not raise error."""
        tmp_store.revoke_api_key("nonexistent")

    def test_list_projects_returns_all_projects(self, tmp_store):
        """list_projects should return all created projects."""
        tmp_store.create_api_key("proj1", "alice")
        tmp_store.create_api_key("proj2", "bob")

        projects = tmp_store.list_projects()

        assert "proj1" in projects
        assert "proj2" in projects
        assert projects["proj1"]["developer_id"] == "alice"
        assert projects["proj2"]["developer_id"] == "bob"

    def test_api_key_stored_as_hash_not_plaintext(self, tmp_store):
        """API keys must be stored as hashes, never plaintext."""
        api_key = tmp_store.create_api_key("proj1", "alice")

        with open(tmp_store.store_path, "r") as f:
            store_data = json.load(f)

        raw_content = json.dumps(store_data)
        assert api_key not in raw_content

        assert "api_key_hash" in store_data["proj1"]
        assert len(store_data["proj1"]["api_key_hash"]) == 64

    def test_created_at_stored(self, tmp_store):
        """created_at timestamp should be stored."""
        tmp_store.create_api_key("proj1", "alice")

        projects = tmp_store.list_projects()
        assert "created_at" in projects["proj1"]

    def test_empty_store_initializes_correctly(self, tmp_path):
        """New store should initialize with empty JSON."""
        store_path = tmp_path / "new_store.json"
        APIKeyStore(store_path=store_path)

        assert store_path.exists()
        with open(store_path, "r") as f:
            data = json.load(f)
        assert data == {}

    def test_validate_is_idempotent(self, tmp_store):
        """Validating same key multiple times should give same result."""
        api_key = tmp_store.create_api_key("proj1", "alice")

        assert tmp_store.validate_api_key("proj1", api_key) is True
        assert tmp_store.validate_api_key("proj1", api_key) is True
        assert tmp_store.validate_api_key("proj1", api_key) is True

"""
Unit tests for FastAPI authentication dependencies.

Tests the get_project_context dependency in isolation.
"""

import pytest

from wfc.servers.rest_api.auth import APIKeyStore
from wfc.servers.rest_api.dependencies import get_api_key_store, get_project_context


class TestGetApiKeyStore:
    """Test get_api_key_store dependency."""

    def test_returns_api_key_store_instance(self):
        """Should return an APIKeyStore instance."""
        store = get_api_key_store()
        assert isinstance(store, APIKeyStore)

    def test_returns_same_instance(self):
        """Should return the same singleton instance on repeated calls."""
        store1 = get_api_key_store()
        store2 = get_api_key_store()
        assert store1 is store2


class TestGetProjectContext:
    """Test get_project_context dependency."""

    @pytest.fixture
    def tmp_store(self, tmp_path):
        """Create temporary API key store with a test project."""
        store_path = tmp_path / "api_keys.json"
        store = APIKeyStore(store_path=store_path)
        return store

    @pytest.mark.asyncio
    async def test_valid_credentials_return_context(self, tmp_store):
        """Valid credentials should return a ProjectContext."""
        api_key = tmp_store.create_api_key("test-proj", "alice")

        context = await get_project_context(
            x_project_id="test-proj",
            authorization=f"Bearer {api_key}",
            api_key_store=tmp_store,
        )

        assert context.project_id == "test-proj"
        assert context.developer_id == "alice"

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix_raises_401(self, tmp_store):
        """Authorization without 'Bearer ' prefix should raise 401."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_project_context(
                x_project_id="test-proj",
                authorization="Basic some-creds",
                api_key_store=tmp_store,
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_401(self, tmp_store):
        """Invalid API key should raise 401."""
        from fastapi import HTTPException

        tmp_store.create_api_key("test-proj", "alice")

        with pytest.raises(HTTPException) as exc_info:
            await get_project_context(
                x_project_id="test-proj",
                authorization="Bearer wrong-key",
                api_key_store=tmp_store,
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_project_raises_401(self, tmp_store):
        """Non-existent project should raise 401."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_project_context(
                x_project_id="nonexistent",
                authorization="Bearer some-key",
                api_key_store=tmp_store,
            )

        assert exc_info.value.status_code == 401

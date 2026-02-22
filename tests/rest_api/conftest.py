"""
Shared fixtures for REST API integration tests.

Provides test client, project setup, and dependency overrides.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from wfc.servers.rest_api.main import app

from wfc.servers.rest_api.auth import APIKeyStore
from wfc.servers.rest_api.background import ReviewStatusStore
from wfc.servers.rest_api.dependencies import get_api_key_store


@pytest.fixture
def tmp_api_key_store(tmp_path):
    """Create temporary API key store."""
    store_path = tmp_path / "api_keys.json"
    return APIKeyStore(store_path=store_path)


@pytest.fixture
def tmp_review_store(tmp_path):
    """Create temporary review status store."""
    reviews_dir = tmp_path / "reviews"
    return ReviewStatusStore(reviews_dir=reviews_dir)


@pytest.fixture
def setup_project(tmp_api_key_store):
    """Set up test project with API key and dependency overrides."""
    api_key = tmp_api_key_store.create_api_key("test-proj", "alice")

    app.dependency_overrides[get_api_key_store] = lambda: tmp_api_key_store

    yield {
        "project_id": "test-proj",
        "developer_id": "alice",
        "api_key": api_key,
        "api_key_store": tmp_api_key_store,
    }

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(setup_project):
    """Create async test client with auth headers pre-configured."""
    transport = ASGITransport(app=app)
    headers = {
        "X-Project-ID": setup_project["project_id"],
        "Authorization": f"Bearer {setup_project['api_key']}",
    }
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=headers,
    ) as ac:
        yield ac

"""
Unit tests for FastAPI main application setup.

Integration endpoint tests are in test_review_endpoints.py,
test_project_endpoints.py, and test_resource_endpoints.py.
This file validates app configuration and middleware.
"""

import pytest

from wfc.servers.rest_api.main import MAX_REQUEST_SIZE, app


class TestAppConfiguration:
    """Test FastAPI app is configured correctly."""

    def test_app_title(self):
        """App should have correct title."""
        assert app.title == "WFC REST API"

    def test_app_version(self):
        """App should have version 1.0.0."""
        assert app.version == "1.0.0"

    def test_openapi_url_configured(self):
        """OpenAPI URL should be configured."""
        assert app.openapi_url == "/openapi.json"

    def test_docs_url_configured(self):
        """Docs URL should be configured."""
        assert app.docs_url == "/docs"

    def test_routers_included(self):
        """All routers should be included in the app."""
        route_paths = [route.path for route in app.routes]
        assert any("/v1/reviews" in p for p in route_paths)
        assert any("/v1/projects" in p for p in route_paths)
        assert any("/v1/resources" in p for p in route_paths)

    def test_health_check_route_exists(self):
        """Health check route at / should exist."""
        route_paths = [route.path for route in app.routes]
        assert "/" in route_paths


class TestRequestSizeLimit:
    """Test request size configuration."""

    def test_max_request_size_is_1mb(self):
        """Max request size should be 1MB."""
        assert MAX_REQUEST_SIZE == 1_000_000


@pytest.mark.asyncio
class TestHealthCheckEndpoint:
    """Test health check endpoint via client."""

    async def test_health_check_returns_healthy(self, client):
        """GET / should return healthy status."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "wfc-rest-api"
        assert data["version"] == "1.0.0"

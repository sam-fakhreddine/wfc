"""
Integration tests for resource monitoring endpoints.

TDD RED phase: these tests define expected behavior for resource routes.
"""

import pytest


@pytest.mark.asyncio
class TestResourceEndpoints:
    """Integration tests for resource endpoints."""

    async def test_get_pool_status_returns_metrics(self, auth_client):
        """GET /v1/resources/pool should return pool metrics."""
        response = await auth_client.get("/v1/resources/pool")

        assert response.status_code == 200
        data = response.json()
        assert "max_worktrees" in data
        assert "active_worktrees" in data
        assert "available_capacity" in data
        assert "orphaned_worktrees" in data

    async def test_get_rate_limit_status_returns_metrics(self, auth_client):
        """GET /v1/resources/rate-limit should return rate limit metrics."""
        response = await auth_client.get("/v1/resources/rate-limit")

        assert response.status_code == 200
        data = response.json()
        assert "capacity" in data
        assert "refill_rate" in data
        assert "available_tokens" in data
        assert "tokens_used" in data

    async def test_pool_endpoint_requires_auth(self, client):
        """GET /v1/resources/pool should require authentication."""
        response = await client.get("/v1/resources/pool")

        assert response.status_code == 422

    async def test_rate_limit_endpoint_requires_auth(self, client):
        """GET /v1/resources/rate-limit should require authentication."""
        response = await client.get("/v1/resources/rate-limit")

        assert response.status_code == 422


@pytest.mark.asyncio
class TestHealthCheck:
    """Integration tests for health check endpoint."""

    async def test_health_check_returns_200(self, client):
        """GET / should return health check response."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "wfc-rest-api"
        assert "version" in data

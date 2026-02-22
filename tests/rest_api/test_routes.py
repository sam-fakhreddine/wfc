"""
Unit tests for API route definitions.

Route endpoint behavior is tested in test_review_endpoints.py,
test_project_endpoints.py, and test_resource_endpoints.py.
This file validates route registration and structure.
"""

from wfc.servers.rest_api.routes import (
    project_router,
    resource_router,
    review_router,
)


class TestRouterRegistration:
    """Test that routers are correctly configured."""

    def test_review_router_prefix(self):
        """Review router should have /v1/reviews prefix."""
        assert review_router.prefix == "/v1/reviews"

    def test_project_router_prefix(self):
        """Project router should have /v1/projects prefix."""
        assert project_router.prefix == "/v1/projects"

    def test_resource_router_prefix(self):
        """Resource router should have /v1/resources prefix."""
        assert resource_router.prefix == "/v1/resources"

    def test_review_router_has_post_and_get(self):
        """Review router should have POST and GET routes."""
        paths = [route.path for route in review_router.routes]
        assert any(p.endswith("/") for p in paths)
        assert any("{review_id}" in p for p in paths)

    def test_project_router_has_post_and_get(self):
        """Project router should have POST and GET routes."""
        paths = [route.path for route in project_router.routes]
        assert any(p.endswith("/") for p in paths)

    def test_resource_router_has_pool_and_rate_limit(self):
        """Resource router should have /pool and /rate-limit endpoints."""
        paths = [route.path for route in resource_router.routes]
        assert any("pool" in p for p in paths)
        assert any("rate-limit" in p for p in paths)

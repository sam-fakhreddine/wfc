"""
Unit tests for per-project rate limiting (Issue #65).

Tests per-project token bucket rate limiting and resource quotas.
"""

import time

import pytest

from wfc.shared.rate_limiting import ProjectRateLimiter


class TestProjectRateLimiter:
    """Test per-project rate limiting functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter with fast refill for testing."""
        return ProjectRateLimiter(
            default_reviews_per_hour=10,
            default_concurrent_reviews=2,
            refill_interval=0.1,
        )

    def test_create_project_quota(self, rate_limiter):
        """Creating a project should initialize its quota."""
        rate_limiter.create_project_quota("proj1")

        assert "proj1" in rate_limiter.quotas
        assert rate_limiter.quotas["proj1"]["reviews_per_hour"] == 10
        assert rate_limiter.quotas["proj1"]["concurrent_reviews"] == 2

    def test_create_project_quota_with_custom_limits(self, rate_limiter):
        """Project quota should accept custom limits."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=20, concurrent_reviews=5)

        assert rate_limiter.quotas["proj1"]["reviews_per_hour"] == 20
        assert rate_limiter.quotas["proj1"]["concurrent_reviews"] == 5

    def test_acquire_within_rate_limit_succeeds(self, rate_limiter):
        """Acquiring tokens within rate limit should succeed."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=10)

        assert rate_limiter.acquire("proj1", tokens=1) is True

    def test_acquire_exceeding_rate_limit_fails(self, rate_limiter):
        """Acquiring too many tokens should fail."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=2)

        assert rate_limiter.acquire("proj1", tokens=1) is True
        assert rate_limiter.acquire("proj1", tokens=1) is True
        assert rate_limiter.acquire("proj1", tokens=1) is False

    def test_acquire_for_nonexistent_project_creates_quota(self, rate_limiter):
        """Acquiring for non-existent project should auto-create quota."""
        assert rate_limiter.acquire("proj1", tokens=1) is True

        assert "proj1" in rate_limiter.quotas

    def test_concurrent_reviews_enforced(self, rate_limiter):
        """Concurrent review limit should be enforced."""
        rate_limiter.create_project_quota("proj1", concurrent_reviews=2)

        assert rate_limiter.start_review("proj1") is True
        assert rate_limiter.start_review("proj1") is True
        assert rate_limiter.start_review("proj1") is False

    def test_finish_review_releases_slot(self, rate_limiter):
        """Finishing a review should release a concurrent slot."""
        rate_limiter.create_project_quota("proj1", concurrent_reviews=1)

        assert rate_limiter.start_review("proj1") is True
        assert rate_limiter.start_review("proj1") is False

        rate_limiter.finish_review("proj1")

        assert rate_limiter.start_review("proj1") is True

    def test_get_quota_status_returns_usage(self, rate_limiter):
        """get_quota_status should return current usage."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=10, concurrent_reviews=3)
        rate_limiter.acquire("proj1", tokens=5)
        rate_limiter.start_review("proj1")
        rate_limiter.start_review("proj1")

        status = rate_limiter.get_quota_status("proj1")

        assert status["reviews_per_hour"] == 10
        assert status["concurrent_reviews"] == 3
        assert status["tokens_available"] == 5
        assert status["active_reviews"] == 2

    def test_multiple_projects_isolated(self, rate_limiter):
        """Different projects should have isolated rate limits."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=2)
        rate_limiter.create_project_quota("proj2", reviews_per_hour=2)

        assert rate_limiter.acquire("proj1", tokens=1) is True
        assert rate_limiter.acquire("proj1", tokens=1) is True
        assert rate_limiter.acquire("proj1", tokens=1) is False

        assert rate_limiter.acquire("proj2", tokens=1) is True

    def test_tokens_refill_over_time(self, rate_limiter):
        """Tokens should refill over time."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=3600)

        assert rate_limiter.acquire("proj1", tokens=3600) is True
        assert rate_limiter.acquire("proj1", tokens=1) is False

        time.sleep(1.2)

        assert rate_limiter.acquire("proj1", tokens=1) is True

    def test_update_project_quota(self, rate_limiter):
        """Updating project quota should change limits."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=10)
        rate_limiter.update_project_quota("proj1", reviews_per_hour=20)

        assert rate_limiter.quotas["proj1"]["reviews_per_hour"] == 20

    def test_delete_project_quota(self, rate_limiter):
        """Deleting project quota should remove all tracking."""
        rate_limiter.create_project_quota("proj1")
        rate_limiter.delete_project_quota("proj1")

        assert "proj1" not in rate_limiter.quotas

    def test_list_all_quotas(self, rate_limiter):
        """list_quotas should return all project quotas."""
        rate_limiter.create_project_quota("proj1", reviews_per_hour=10)
        rate_limiter.create_project_quota("proj2", reviews_per_hour=20)

        quotas = rate_limiter.list_quotas()

        assert len(quotas) == 2
        assert "proj1" in quotas
        assert "proj2" in quotas
        assert quotas["proj1"]["reviews_per_hour"] == 10
        assert quotas["proj2"]["reviews_per_hour"] == 20

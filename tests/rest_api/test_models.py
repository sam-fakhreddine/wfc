"""
Unit tests for REST API Pydantic models.

TDD RED phase: these tests define expected behavior for models.py
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from wfc.servers.rest_api.models import (
    ErrorResponse,
    PoolStatusResponse,
    ProjectCreateRequest,
    RateLimitStatusResponse,
    ReviewFinding,
    ReviewStatus,
    ReviewStatusResponse,
    ReviewSubmitRequest,
)


class TestReviewSubmitRequest:
    """Test ReviewSubmitRequest validation."""

    def test_valid_request(self):
        """Valid request should pass validation."""
        request = ReviewSubmitRequest(
            diff_content="diff content",
            files=["file1.py", "file2.py"],
        )
        assert request.diff_content == "diff content"
        assert len(request.files) == 2

    def test_empty_diff_content_fails(self):
        """Empty diff_content should fail validation."""
        with pytest.raises(ValidationError):
            ReviewSubmitRequest(diff_content="", files=[])

    def test_empty_files_allowed(self):
        """Empty files list should be allowed."""
        request = ReviewSubmitRequest(diff_content="diff", files=[])
        assert request.files == []

    def test_files_defaults_to_empty_list(self):
        """Files should default to empty list if not provided."""
        request = ReviewSubmitRequest(diff_content="diff")
        assert request.files == []

    def test_empty_string_in_files_fails(self):
        """Empty string in files list should fail validation."""
        with pytest.raises(ValidationError):
            ReviewSubmitRequest(diff_content="diff", files=["good.py", ""])

    def test_whitespace_only_file_fails(self):
        """Whitespace-only file name should fail validation."""
        with pytest.raises(ValidationError):
            ReviewSubmitRequest(diff_content="diff", files=["  "])


class TestReviewStatus:
    """Test ReviewStatus enum."""

    def test_all_statuses_defined(self):
        """All expected statuses should be defined."""
        assert ReviewStatus.PENDING == "pending"
        assert ReviewStatus.IN_PROGRESS == "in_progress"
        assert ReviewStatus.COMPLETED == "completed"
        assert ReviewStatus.FAILED == "failed"

    def test_status_is_string_enum(self):
        """ReviewStatus values should be strings."""
        assert isinstance(ReviewStatus.PENDING, str)


class TestProjectCreateRequest:
    """Test ProjectCreateRequest validation."""

    def test_valid_project_id(self):
        """Valid project_id should pass."""
        request = ProjectCreateRequest(
            project_id="my-project-123",
            developer_id="alice",
            repo_path="/absolute/path",
        )
        assert request.project_id == "my-project-123"

    def test_invalid_project_id_characters(self):
        """Invalid characters in project_id should fail."""
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                project_id="invalid@project!",
                developer_id="alice",
                repo_path="/absolute/path",
            )

    def test_relative_repo_path_fails(self):
        """Relative repo_path should fail."""
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                project_id="proj1",
                developer_id="alice",
                repo_path="relative/path",
            )

    def test_empty_project_id_fails(self):
        """Empty project_id should fail."""
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                project_id="",
                developer_id="alice",
                repo_path="/absolute/path",
            )

    def test_too_long_project_id_fails(self):
        """project_id longer than 64 chars should fail."""
        with pytest.raises(ValidationError):
            ProjectCreateRequest(
                project_id="a" * 65,
                developer_id="alice",
                repo_path="/absolute/path",
            )

    def test_underscore_and_hyphen_allowed(self):
        """Underscores and hyphens should be allowed in IDs."""
        request = ProjectCreateRequest(
            project_id="my_project-1",
            developer_id="dev_user-2",
            repo_path="/path/to/repo",
        )
        assert request.project_id == "my_project-1"
        assert request.developer_id == "dev_user-2"


class TestReviewFinding:
    """Test ReviewFinding validation."""

    def test_confidence_in_range(self):
        """Confidence must be 0-100."""
        finding = ReviewFinding(
            reviewer="Security",
            severity="HIGH",
            category="XSS",
            description="Potential XSS",
            confidence=85,
        )
        assert finding.confidence == 85

    def test_confidence_zero_allowed(self):
        """Confidence of 0 should be valid."""
        finding = ReviewFinding(
            reviewer="Security",
            severity="LOW",
            category="Info",
            description="Informational",
            confidence=0,
        )
        assert finding.confidence == 0

    def test_confidence_hundred_allowed(self):
        """Confidence of 100 should be valid."""
        finding = ReviewFinding(
            reviewer="Security",
            severity="HIGH",
            category="Critical",
            description="Critical issue",
            confidence=100,
        )
        assert finding.confidence == 100

    def test_confidence_over_100_fails(self):
        """Confidence >100 should fail."""
        with pytest.raises(ValidationError):
            ReviewFinding(
                reviewer="Security",
                severity="HIGH",
                category="XSS",
                description="Potential XSS",
                confidence=150,
            )

    def test_confidence_negative_fails(self):
        """Confidence <0 should fail."""
        with pytest.raises(ValidationError):
            ReviewFinding(
                reviewer="Security",
                severity="HIGH",
                category="XSS",
                description="Potential XSS",
                confidence=-1,
            )

    def test_optional_fields(self):
        """file_path and line_number should be optional."""
        finding = ReviewFinding(
            reviewer="Security",
            severity="HIGH",
            category="XSS",
            description="Potential XSS",
            confidence=85,
        )
        assert finding.file_path is None
        assert finding.line_number is None


class TestReviewStatusResponse:
    """Test ReviewStatusResponse."""

    def test_minimal_response(self):
        """Minimal response with required fields only."""
        response = ReviewStatusResponse(
            review_id="test-id",
            status=ReviewStatus.PENDING,
            project_id="proj1",
            developer_id="alice",
            submitted_at=datetime.now(timezone.utc),
        )
        assert response.completed_at is None
        assert response.consensus_score is None
        assert response.passed is None
        assert response.findings == []
        assert response.error_message is None

    def test_consensus_score_range(self):
        """consensus_score must be 0.0-10.0."""
        with pytest.raises(ValidationError):
            ReviewStatusResponse(
                review_id="test-id",
                status=ReviewStatus.COMPLETED,
                project_id="proj1",
                developer_id="alice",
                submitted_at=datetime.now(timezone.utc),
                consensus_score=11.0,
            )


class TestPoolStatusResponse:
    """Test PoolStatusResponse."""

    def test_valid_pool_status(self):
        """Valid pool status should pass."""
        response = PoolStatusResponse(
            max_worktrees=10,
            active_worktrees=3,
            available_capacity=7,
            orphaned_worktrees=0,
        )
        assert response.max_worktrees == 10
        assert response.available_capacity == 7


class TestRateLimitStatusResponse:
    """Test RateLimitStatusResponse."""

    def test_valid_rate_limit_status(self):
        """Valid rate limit status should pass."""
        response = RateLimitStatusResponse(
            capacity=10,
            refill_rate=10.0,
            available_tokens=8.5,
            tokens_used=1.5,
        )
        assert response.capacity == 10
        assert response.available_tokens == 8.5


class TestErrorResponse:
    """Test ErrorResponse."""

    def test_error_response_with_defaults(self):
        """ErrorResponse should have timestamp default."""
        response = ErrorResponse(error="Something went wrong")
        assert response.error == "Something went wrong"
        assert response.detail is None
        assert response.timestamp is not None

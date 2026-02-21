"""
Unit tests for review status tracking.

TDD RED phase: these tests define expected behavior for background.py
"""

import pytest

from wfc.servers.rest_api.background import ReviewStatusStore
from wfc.servers.rest_api.models import ReviewStatus


class TestReviewStatusStore:
    """Test ReviewStatusStore functionality."""

    @pytest.fixture
    def tmp_store(self, tmp_path):
        """Create temporary review status store."""
        reviews_dir = tmp_path / "reviews"
        return ReviewStatusStore(reviews_dir=reviews_dir)

    def test_create_review_generates_uuid(self, tmp_store):
        """create_review should generate unique UUID."""
        review_id = tmp_store.create_review("proj1", "alice")

        assert len(review_id) == 36
        assert "-" in review_id

    def test_create_review_generates_unique_ids(self, tmp_store):
        """Each review should get a unique ID."""
        id1 = tmp_store.create_review("proj1", "alice")
        id2 = tmp_store.create_review("proj1", "alice")

        assert id1 != id2

    def test_get_review_returns_pending_status(self, tmp_store):
        """Newly created review should have PENDING status."""
        review_id = tmp_store.create_review("proj1", "alice")

        review = tmp_store.get_review(review_id)

        assert review is not None
        assert review.status == ReviewStatus.PENDING
        assert review.project_id == "proj1"
        assert review.developer_id == "alice"

    def test_update_status_changes_status(self, tmp_store):
        """update_status should change review status."""
        review_id = tmp_store.create_review("proj1", "alice")

        tmp_store.update_status(review_id, ReviewStatus.IN_PROGRESS)

        review = tmp_store.get_review(review_id)
        assert review.status == ReviewStatus.IN_PROGRESS

    def test_complete_review_sets_results(self, tmp_store):
        """complete_review should set results and COMPLETED status."""
        review_id = tmp_store.create_review("proj1", "alice")

        findings = [
            {
                "reviewer": "Security",
                "severity": "HIGH",
                "category": "XSS",
                "description": "Potential XSS",
                "file_path": "test.py",
                "line_number": 42,
                "confidence": 85,
            }
        ]

        tmp_store.complete_review(review_id, 8.5, True, findings)

        review = tmp_store.get_review(review_id)
        assert review.status == ReviewStatus.COMPLETED
        assert review.consensus_score == 8.5
        assert review.passed is True
        assert len(review.findings) == 1
        assert review.findings[0].reviewer == "Security"
        assert review.completed_at is not None

    def test_fail_review_sets_error(self, tmp_store):
        """fail_review should set error message and FAILED status."""
        review_id = tmp_store.create_review("proj1", "alice")

        tmp_store.fail_review(review_id, "Something went wrong")

        review = tmp_store.get_review(review_id)
        assert review.status == ReviewStatus.FAILED
        assert review.error_message == "Something went wrong"
        assert review.completed_at is not None

    def test_get_nonexistent_review_returns_none(self, tmp_store):
        """get_review with invalid ID should return None."""
        review = tmp_store.get_review("nonexistent-uuid")

        assert review is None

    def test_review_file_created_on_disk(self, tmp_store):
        """Review should be persisted to disk as JSON file."""
        review_id = tmp_store.create_review("proj1", "alice")

        review_path = tmp_store.reviews_dir / f"{review_id}.json"
        assert review_path.exists()

    def test_submitted_at_timestamp_set(self, tmp_store):
        """submitted_at should be set on creation."""
        review_id = tmp_store.create_review("proj1", "alice")

        review = tmp_store.get_review(review_id)
        assert review.submitted_at is not None

    def test_initial_review_has_no_findings(self, tmp_store):
        """Newly created review should have empty findings."""
        review_id = tmp_store.create_review("proj1", "alice")

        review = tmp_store.get_review(review_id)
        assert review.findings == []
        assert review.consensus_score is None
        assert review.passed is None
        assert review.error_message is None

    def test_list_reviews_for_project(self, tmp_store):
        """list_reviews should return reviews for a specific project."""
        id1 = tmp_store.create_review("proj1", "alice")
        id2 = tmp_store.create_review("proj1", "alice")
        id3 = tmp_store.create_review("proj2", "bob")

        reviews = tmp_store.list_reviews("proj1")

        review_ids = [r.review_id for r in reviews]
        assert id1 in review_ids
        assert id2 in review_ids
        assert id3 not in review_ids

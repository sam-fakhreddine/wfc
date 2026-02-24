"""
Integration tests for review endpoints.

TDD RED phase: these tests define expected behavior for review routes.
"""

import pytest


@pytest.mark.asyncio
class TestReviewEndpoints:
    """Integration tests for review endpoints."""

    async def test_submit_review_returns_202_with_review_id(self, auth_client, setup_project):
        """POST /v1/reviews should return 202 with review_id."""
        response = await auth_client.post(
            "/v1/reviews/",
            json={
                "diff_content": "sample diff content",
                "files": ["test.py"],
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert "review_id" in data
        assert data["status"] == "pending"
        assert data["project_id"] == "test-proj"

    async def test_submit_review_without_auth_returns_422(self, client):
        """POST /v1/reviews without auth headers should return 422 (missing required header)."""
        response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": []},
        )

        assert response.status_code == 422

    async def test_submit_review_with_invalid_api_key_returns_401(self, client, setup_project):
        """POST /v1/reviews with invalid API key should return 401."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": "Bearer invalid-key",
        }

        response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": []},
            headers=headers,
        )

        assert response.status_code == 401

    async def test_submit_review_with_bad_bearer_format_returns_401(self, client, setup_project):
        """POST /v1/reviews with malformed Authorization header should return 401."""
        headers = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": "Basic some-creds",
        }

        response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": []},
            headers=headers,
        )

        assert response.status_code == 401

    async def test_submit_review_empty_diff_returns_422(self, auth_client):
        """POST /v1/reviews with empty diff_content should return 422."""
        response = await auth_client.post(
            "/v1/reviews/",
            json={"diff_content": "", "files": []},
        )

        assert response.status_code == 422

    async def test_get_review_status_returns_review(self, auth_client, setup_project):
        """GET /v1/reviews/{id} should return review status."""
        submit_response = await auth_client.post(
            "/v1/reviews/",
            json={"diff_content": "diff content", "files": ["test.py"]},
        )
        review_id = submit_response.json()["review_id"]

        status_response = await auth_client.get(f"/v1/reviews/{review_id}")

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["review_id"] == review_id
        assert data["status"] in ["pending", "in_progress", "completed", "failed"]

    async def test_get_nonexistent_review_returns_404(self, auth_client):
        """GET /v1/reviews/{id} for non-existent review should return 404."""
        response = await auth_client.get("/v1/reviews/nonexistent-uuid")

        assert response.status_code == 404

    async def test_get_review_other_project_returns_403(self, client, setup_project):
        """GET /v1/reviews/{id} from different project should return 403."""
        headers1 = {
            "X-Project-ID": setup_project["project_id"],
            "Authorization": f"Bearer {setup_project['api_key']}",
        }

        submit_response = await client.post(
            "/v1/reviews/",
            json={"diff_content": "diff", "files": []},
            headers=headers1,
        )
        review_id = submit_response.json()["review_id"]

        api_key_store = setup_project["api_key_store"]
        api_key2 = api_key_store.create_api_key("proj2", "bob")

        headers2 = {
            "X-Project-ID": "proj2",
            "Authorization": f"Bearer {api_key2}",
        }

        status_response = await client.get(
            f"/v1/reviews/{review_id}",
            headers=headers2,
        )

        assert status_response.status_code == 403

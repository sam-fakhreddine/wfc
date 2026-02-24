"""
Integration tests for project endpoints.

TDD RED phase: these tests define expected behavior for project routes.
"""

import pytest


@pytest.mark.asyncio
class TestProjectEndpoints:
    """Integration tests for project endpoints."""

    async def test_create_project_returns_201_with_api_key(self, client, setup_project):
        """POST /v1/projects should create project and return API key."""
        response = await client.post(
            "/v1/projects/",
            json={
                "project_id": "new-proj",
                "developer_id": "alice",
                "repo_path": "/absolute/path",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == "new-proj"
        assert "api_key" in data
        assert len(data["api_key"]) > 30

    async def test_create_duplicate_project_returns_409(self, client, setup_project):
        """Creating duplicate project should return 409."""
        payload = {
            "project_id": "dup-proj",
            "developer_id": "alice",
            "repo_path": "/absolute/path",
        }

        await client.post("/v1/projects/", json=payload)

        response = await client.post("/v1/projects/", json=payload)

        assert response.status_code == 409

    async def test_create_project_invalid_id_returns_422(self, client, setup_project):
        """Creating project with invalid ID should return 422."""
        response = await client.post(
            "/v1/projects/",
            json={
                "project_id": "invalid@id!",
                "developer_id": "alice",
                "repo_path": "/absolute/path",
            },
        )

        assert response.status_code == 422

    async def test_create_project_relative_path_returns_422(self, client, setup_project):
        """Creating project with relative path should return 422."""
        response = await client.post(
            "/v1/projects/",
            json={
                "project_id": "proj1",
                "developer_id": "alice",
                "repo_path": "relative/path",
            },
        )

        assert response.status_code == 422

    async def test_list_projects_returns_all_projects(self, client, setup_project):
        """GET /v1/projects should list all projects."""
        await client.post(
            "/v1/projects/",
            json={"project_id": "proj-a", "developer_id": "alice", "repo_path": "/path/a"},
        )
        await client.post(
            "/v1/projects/",
            json={"project_id": "proj-b", "developer_id": "bob", "repo_path": "/path/b"},
        )

        response = await client.get("/v1/projects/")

        assert response.status_code == 200
        data = response.json()
        project_ids = [p["project_id"] for p in data["projects"]]
        assert "proj-a" in project_ids
        assert "proj-b" in project_ids

    async def test_list_projects_does_not_expose_api_key_hashes(self, client, setup_project):
        """GET /v1/projects should not expose API key hashes."""
        await client.post(
            "/v1/projects/",
            json={"project_id": "safe-proj", "developer_id": "alice", "repo_path": "/path"},
        )

        response = await client.get("/v1/projects/")
        data = response.json()

        for project in data["projects"]:
            assert "api_key_hash" not in project
            assert "api_key" not in project

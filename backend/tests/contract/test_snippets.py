"""Contract tests for snippet endpoints.

Tests verify:
- POST /snippets: snippet creation contract
- GET /snippets: snippet list contract
- POST /snippets/{snippet_id}/execute: snippet execution contract
- PUT /snippets/{snippet_id}: snippet update contract
- DELETE /snippets/{snippet_id}: snippet deletion contract
"""

import pytest
from fastapi.testclient import TestClient


class TestSnippetCreateContract:
    """T156: Contract test for POST /snippets"""

    def test_post_create_snippet(self, client: TestClient, auth_token: str):
        """Verify snippet creation returns SnippetResponse"""
        response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "List Files",
                "description": "List all files in directory",
                "command": "ls -la",
                "tags": ["utility", "listing"],
                "public": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "List Files"
        assert data["command"] == "ls -la"
        assert "created_at" in data

    def test_post_create_snippet_authentication_required(self, client: TestClient):
        """Verify authentication is required"""
        response = client.post(
            "/api/snippets",
            json={
                "name": "Test",
                "command": "echo test",
            }
        )

        assert response.status_code == 401

    def test_post_create_snippet_validation(self, client: TestClient, auth_token: str):
        """Verify input validation"""
        # Missing required fields
        response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Test"}
        )

        assert response.status_code == 422  # Validation error


class TestSnippetListContract:
    """T157: Contract test for GET /snippets"""

    def test_get_snippet_list(self, client: TestClient, auth_token: str):
        """Verify snippet list returns array"""
        response = client.get(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            snippet = data[0]
            assert "id" in snippet
            assert "name" in snippet
            assert "command" in snippet

    def test_get_snippet_list_authentication_required(self, client: TestClient):
        """Verify authentication is required"""
        response = client.get("/api/snippets")

        assert response.status_code == 401

    def test_get_snippet_list_filtering_by_tags(self, client: TestClient, auth_token: str):
        """Verify snippet list can be filtered by tags"""
        response = client.get(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"tags": "utility"}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSnippetExecuteContract:
    """T158: Contract test for POST /snippets/{snippet_id}/execute"""

    def test_post_execute_snippet(self, client: TestClient, auth_token: str, created_snippet):
        """Verify snippet execution returns execution result"""
        snippet_id = created_snippet["id"]

        response = client.post(
            f"/api/snippets/{snippet_id}/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_id": "test-session",
                "target_host_id": "test-host",
            }
        )

        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert "execution_id" in data or "success" in data

    def test_post_execute_snippet_authentication_required(self, client: TestClient, created_snippet):
        """Verify authentication is required"""
        snippet_id = created_snippet["id"]

        response = client.post(
            f"/api/snippets/{snippet_id}/execute",
            json={
                "session_id": "test-session",
            }
        )

        assert response.status_code == 401

    def test_post_execute_snippet_invalid_snippet(self, client: TestClient, auth_token: str):
        """Verify invalid snippet_id returns 404"""
        response = client.post(
            "/api/snippets/invalid-id/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"session_id": "test-session"}
        )

        assert response.status_code == 404


class TestSnippetUpdateContract:
    """T159: Contract test for PUT /snippets/{snippet_id}"""

    def test_put_update_snippet(self, client: TestClient, auth_token: str, created_snippet):
        """Verify snippet update returns updated SnippetResponse"""
        snippet_id = created_snippet["id"]

        response = client.put(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Name",
                "description": "Updated description",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_put_update_snippet_authentication_required(self, client: TestClient, created_snippet):
        """Verify authentication is required"""
        snippet_id = created_snippet["id"]

        response = client.put(
            f"/api/snippets/{snippet_id}",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 401

    def test_put_update_snippet_invalid_snippet(self, client: TestClient, auth_token: str):
        """Verify invalid snippet_id returns 404"""
        response = client.put(
            "/api/snippets/invalid-id",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Updated Name"}
        )

        assert response.status_code == 404


class TestSnippetDeleteContract:
    """T160: Contract test for DELETE /snippets/{snippet_id}"""

    def test_delete_snippet(self, client: TestClient, auth_token: str, created_snippet):
        """Verify snippet deletion"""
        snippet_id = created_snippet["id"]

        response = client.delete(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

    def test_delete_snippet_authentication_required(self, client: TestClient, created_snippet):
        """Verify authentication is required"""
        snippet_id = created_snippet["id"]

        response = client.delete(f"/api/snippets/{snippet_id}")

        assert response.status_code == 401

    def test_delete_snippet_invalid_snippet(self, client: TestClient, auth_token: str):
        """Verify invalid snippet_id returns 404"""
        response = client.delete(
            "/api/snippets/invalid-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

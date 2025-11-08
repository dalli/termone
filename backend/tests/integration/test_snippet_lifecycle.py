"""Integration tests for snippet creation and lifecycle operations.

Tests verify:
- Snippet creation with valid configuration
- Snippet list retrieval with filtering
- Snippet retrieval by ID
- Snippet update operations
- Snippet deletion
- Permission enforcement
"""

import pytest
from fastapi.testclient import TestClient


class TestSnippetLifecycle:
    """Test snippet lifecycle operations."""

    def test_create_snippet(self, client: TestClient, auth_token: str):
        """Verify snippet creation"""
        response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Check Disk Space",
                "description": "Show disk usage on target host",
                "command": "df -h | grep -E '/$'",
                "tags": ["disk", "monitoring"],
                "public": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Check Disk Space"
        assert data["command"] == "df -h | grep -E '/$'"
        assert data["tags"] == ["disk", "monitoring"]
        assert data["public"] is False
        assert data["usage_count"] == 0

    def test_create_snippet_minimal(self, client: TestClient, auth_token: str):
        """Verify snippet creation with minimal fields"""
        response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Simple Ping",
                "command": "ping -c 1 8.8.8.8",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Simple Ping"
        assert data["command"] == "ping -c 1 8.8.8.8"
        assert "id" in data

    def test_list_snippets(self, client: TestClient, auth_token: str):
        """Verify snippet list retrieval"""
        # Create a snippet first
        client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Snippet",
                "command": "echo 'test'",
                "tags": ["test"],
            }
        )

        # List snippets
        response = client.get(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(s["name"] == "Test Snippet" for s in data)

    def test_list_snippets_with_tag_filter(self, client: TestClient, auth_token: str):
        """Verify snippet list can be filtered by tags"""
        # Create snippets with different tags
        client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Network Check",
                "command": "netstat -an",
                "tags": ["network"],
            }
        )

        client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Disk Check",
                "command": "df -h",
                "tags": ["disk"],
            }
        )

        # Filter by network tag
        response = client.get(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"tags": "network"}
        )

        assert response.status_code == 200
        data = response.json()
        assert any(s["name"] == "Network Check" for s in data)
        # Disk check should not appear
        assert not any(s["name"] == "Disk Check" for s in data)

    def test_get_snippet_by_id(self, client: TestClient, auth_token: str):
        """Verify snippet retrieval by ID"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Get Test",
                "command": "ls -la",
            }
        )
        snippet_id = create_response.json()["id"]

        # Get snippet
        response = client.get(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == snippet_id
        assert data["name"] == "Get Test"

    def test_update_snippet(self, client: TestClient, auth_token: str):
        """Verify snippet update"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Original Name",
                "command": "original command",
                "tags": ["old"],
            }
        )
        snippet_id = create_response.json()["id"]

        # Update snippet
        response = client.put(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Name",
                "description": "New description",
                "tags": ["updated"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"
        assert data["tags"] == ["updated"]

    def test_delete_snippet(self, client: TestClient, auth_token: str):
        """Verify snippet deletion"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Delete Test",
                "command": "rm -rf /",
            }
        )
        snippet_id = create_response.json()["id"]

        # Delete snippet
        response = client.delete(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404

    def test_snippet_requires_authentication(self, client: TestClient):
        """Verify authentication is required"""
        # Create without auth
        response = client.post(
            "/api/snippets",
            json={
                "name": "Test",
                "command": "echo test",
            }
        )

        assert response.status_code == 401

    def test_snippet_permission_denied_other_user(
        self, client: TestClient, auth_token: str, other_user_token: str
    ):
        """Verify users cannot access other user's snippets"""
        # Create snippet with first user
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Private Snippet",
                "command": "secret command",
            }
        )
        snippet_id = create_response.json()["id"]

        # Try to get with other user
        response = client.get(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {other_user_token}"}
        )

        assert response.status_code == 404

    def test_snippet_public_visible_to_others(self, client: TestClient, auth_token: str, other_user_token: str):
        """Verify public snippets are visible to other users"""
        # Create public snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Public Snippet",
                "command": "public command",
                "public": True,
            }
        )
        snippet_id = create_response.json()["id"]

        # Other user should be able to list it
        response = client.get(
            "/api/snippets",
            headers={"Authorization": f"Bearer {other_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert any(s["id"] == snippet_id for s in data)

    def test_list_with_invalid_tag_format(self, client: TestClient, auth_token: str):
        """Verify list handles various tag formats"""
        # Create snippet with tags
        client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Tagged Snippet",
                "command": "command",
                "tags": ["tag1", "tag2"],
            }
        )

        # List with single tag
        response = client.get(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"tags": "tag1"}
        )
        assert response.status_code == 200

        # List with multiple tags (comma-separated)
        response = client.get(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"tags": "tag1,tag2"}
        )
        assert response.status_code == 200

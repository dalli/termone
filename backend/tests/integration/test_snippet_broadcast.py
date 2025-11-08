"""Integration tests for snippet broadcast execution.

Tests verify:
- Snippet execution in single session
- Snippet broadcast to multiple sessions
- Session validation
- Permission checks for execution
"""

import pytest
from fastapi.testclient import TestClient


class TestSnippetBroadcast:
    """Test snippet broadcast and execution operations."""

    def test_execute_snippet_requires_session(self, client: TestClient, auth_token: str):
        """Verify snippet execution requires a valid session"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Execute Test",
                "command": "echo 'test'",
            }
        )
        snippet_id = create_response.json()["id"]

        # Try to execute without session
        response = client.post(
            f"/api/snippets/{snippet_id}/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_id": "invalid-session",
            }
        )

        # Should fail gracefully
        assert response.status_code in [400, 404]

    def test_execute_snippet_with_valid_session(self, client: TestClient, auth_token: str):
        """Verify snippet execution with valid session"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Valid Execute",
                "command": "whoami",
            }
        )
        snippet_id = create_response.json()["id"]

        # Execute with a session ID (would be from actual terminal session)
        response = client.post(
            f"/api/snippets/{snippet_id}/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_id": "test-session-123",
                "target_host_id": "test-host",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert data["snippet_id"] == snippet_id
        assert data["session_id"] == "test-session-123"

    def test_broadcast_to_single_session(self, client: TestClient, auth_token: str):
        """Verify broadcast to a single session"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Broadcast Single",
                "command": "uptime",
            }
        )
        snippet_id = create_response.json()["id"]

        # Broadcast to one session
        response = client.post(
            f"/api/snippets/{snippet_id}/broadcast",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_ids": ["session-1"],
                "target_host_id": "host-1",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "broadcast_id" in data
        assert data["snippet_id"] == snippet_id
        assert data["sessions"] == ["session-1"]

    def test_broadcast_to_multiple_sessions(self, client: TestClient, auth_token: str):
        """Verify broadcast to multiple sessions"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Broadcast Multiple",
                "command": "free -h",
            }
        )
        snippet_id = create_response.json()["id"]

        # Broadcast to multiple sessions
        session_ids = ["session-1", "session-2", "session-3"]
        response = client.post(
            f"/api/snippets/{snippet_id}/broadcast",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_ids": session_ids,
                "target_host_id": "host-1",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "broadcast_id" in data
        assert len(data["sessions"]) == 3
        assert data["sessions"] == session_ids

    def test_execute_nonexistent_snippet(self, client: TestClient, auth_token: str):
        """Verify executing nonexistent snippet returns 404"""
        response = client.post(
            "/api/snippets/invalid-id/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_id": "session-1",
            }
        )

        assert response.status_code == 404

    def test_broadcast_nonexistent_snippet(self, client: TestClient, auth_token: str):
        """Verify broadcasting nonexistent snippet returns 404"""
        response = client.post(
            "/api/snippets/invalid-id/broadcast",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_ids": ["session-1"],
            }
        )

        assert response.status_code == 404

    def test_execute_other_user_snippet_fails(
        self, client: TestClient, auth_token: str, other_user_token: str
    ):
        """Verify users cannot execute other user's private snippets"""
        # Create snippet with first user
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Private Execute",
                "command": "secret",
            }
        )
        snippet_id = create_response.json()["id"]

        # Try to execute with other user
        response = client.post(
            f"/api/snippets/{snippet_id}/execute",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={
                "session_id": "session-1",
            }
        )

        assert response.status_code == 404

    def test_execute_public_snippet_allowed(
        self, client: TestClient, auth_token: str, other_user_token: str
    ):
        """Verify users can execute public snippets"""
        # Create public snippet with first user
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Public Execute",
                "command": "ls",
                "public": True,
            }
        )
        snippet_id = create_response.json()["id"]

        # Other user should be able to execute
        response = client.post(
            f"/api/snippets/{snippet_id}/execute",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={
                "session_id": "session-1",
            }
        )

        assert response.status_code == 200

    def test_execute_increments_usage_count(self, client: TestClient, auth_token: str):
        """Verify execution increments snippet usage count"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Usage Count Test",
                "command": "date",
            }
        )
        snippet_id = create_response.json()["id"]
        assert create_response.json()["usage_count"] == 0

        # Execute the snippet
        client.post(
            f"/api/snippets/{snippet_id}/execute",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_id": "session-1",
            }
        )

        # Check usage count increased
        response = client.get(
            f"/api/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        data = response.json()
        assert data["usage_count"] >= 1

    def test_execute_without_authentication(self, client: TestClient):
        """Verify execution requires authentication"""
        response = client.post(
            "/api/snippets/some-id/execute",
            json={
                "session_id": "session-1",
            }
        )

        assert response.status_code == 401

    def test_broadcast_without_authentication(self, client: TestClient):
        """Verify broadcast requires authentication"""
        response = client.post(
            "/api/snippets/some-id/broadcast",
            json={
                "session_ids": ["session-1"],
            }
        )

        assert response.status_code == 401

    def test_broadcast_empty_sessions(self, client: TestClient, auth_token: str):
        """Verify broadcast with empty sessions list"""
        # Create a snippet
        create_response = client.post(
            "/api/snippets",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Empty Broadcast",
                "command": "hostname",
            }
        )
        snippet_id = create_response.json()["id"]

        # Broadcast with empty sessions
        response = client.post(
            f"/api/snippets/{snippet_id}/broadcast",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "session_ids": [],
            }
        )

        # Should fail validation
        assert response.status_code == 400

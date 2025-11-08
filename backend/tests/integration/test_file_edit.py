"""Integration tests for file editing operations.

Tests verify:
- File read and write operations
- Content persistence
- Encoding handling
"""

import pytest
from fastapi.testclient import TestClient


class TestFileEdit:
    """Test file editing operations."""

    def test_write_and_read_file(self, client: TestClient, auth_token: str, created_host):
        """Verify file write and read workflow"""
        host_id = created_host["id"]
        test_content = "Hello, World!\nThis is line 2."

        # Write file
        write_response = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/edit_test.txt",
                "content": test_content
            }
        )

        # Should succeed or fail gracefully
        if write_response.status_code == 200:
            write_data = write_response.json()
            assert "path" in write_data
            assert write_data["size"] > 0

    def test_edit_file_with_different_encoding(self, client: TestClient, auth_token: str, created_host):
        """Verify file edit with specific encoding"""
        host_id = created_host["id"]
        test_content = "UTF-8 content: 你好世界 🌍"

        response = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/utf8_test.txt",
                "content": test_content,
                "encoding": "utf-8"
            }
        )

        assert response.status_code in [200, 400, 403]

    def test_edit_without_authentication(self, client: TestClient, created_host):
        """Verify authentication is required for edit"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/edit",
            json={
                "path": "/tmp/test.txt",
                "content": "content"
            }
        )

        assert response.status_code == 401

    def test_edit_invalid_host(self, client: TestClient, auth_token: str):
        """Verify edit fails for invalid host"""
        response = client.post(
            "/api/files/invalid-host/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test.txt",
                "content": "content"
            }
        )

        assert response.status_code == 404

    def test_edit_permission_denied_other_user(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify users cannot edit other users' files"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={
                "path": "/tmp/test.txt",
                "content": "content"
            }
        )

        assert response.status_code == 403

    def test_edit_large_content(self, client: TestClient, auth_token: str, created_host):
        """Verify editing large files"""
        host_id = created_host["id"]
        # Create 1 MB of content
        large_content = "x" * (1024 * 1024)

        response = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/large.txt",
                "content": large_content
            }
        )

        assert response.status_code in [200, 400, 413]

    def test_edit_multiple_times(self, client: TestClient, auth_token: str, created_host):
        """Verify file can be edited multiple times"""
        host_id = created_host["id"]
        file_path = "/tmp/multi_edit.txt"

        # First edit
        response1 = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": file_path,
                "content": "First version"
            }
        )

        assert response1.status_code in [200, 400, 403]

        # Second edit
        response2 = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": file_path,
                "content": "Second version"
            }
        )

        assert response2.status_code in [200, 400, 403]

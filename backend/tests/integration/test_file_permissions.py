"""Integration tests for file permission boundaries.

Tests verify:
- Users cannot access other users' files
- Permission checks at service layer
- Proper access control enforcement
"""

import pytest
from fastapi.testclient import TestClient


class TestFilePermissions:
    """Test file operation permission boundaries."""

    def test_user_cannot_list_other_user_host_files(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot list files on other user's host"""
        host_id = created_host["id"]

        response = client.get(
            f"/api/files/{host_id}/list",
            headers={"Authorization": f"Bearer {other_user_token}"},
            params={"path": "/"}
        )

        assert response.status_code == 403

    def test_user_cannot_upload_to_other_user_host(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot upload files to other user's host"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/upload",
            headers={"Authorization": f"Bearer {other_user_token}"},
            params={"path": "/tmp"},
            files={"file": ("test.txt", b"content", "text/plain")}
        )

        assert response.status_code == 403

    def test_user_cannot_download_from_other_user_host(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot download files from other user's host"""
        host_id = created_host["id"]

        response = client.get(
            f"/api/files/{host_id}/download",
            headers={"Authorization": f"Bearer {other_user_token}"},
            params={"path": "/etc/hostname"}
        )

        assert response.status_code == 403

    def test_user_cannot_delete_other_user_files(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot delete other user's files"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/delete",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={"path": "/tmp/file.txt"}
        )

        assert response.status_code == 403

    def test_user_cannot_edit_other_user_files(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot edit other user's files"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={
                "path": "/tmp/file.txt",
                "content": "new content"
            }
        )

        assert response.status_code == 403

    def test_user_cannot_chmod_other_user_files(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot change permissions on other user's files"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/chmod",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={
                "path": "/tmp/file.txt",
                "mode": 755
            }
        )

        assert response.status_code == 403

    def test_user_cannot_move_other_user_files(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot move other user's files"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/move",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={
                "old_path": "/tmp/old.txt",
                "new_path": "/tmp/new.txt"
            }
        )

        assert response.status_code == 403

    def test_user_cannot_mkdir_other_user_host(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify user cannot create directories on other user's host"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/mkdir",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={"path": "/tmp/newdir"}
        )

        assert response.status_code == 403

    def test_own_host_operations_allowed(self, client: TestClient, auth_token: str, created_host):
        """Verify user can perform operations on own host"""
        host_id = created_host["id"]

        # List should work
        response = client.get(
            f"/api/files/{host_id}/list",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/"}
        )

        assert response.status_code == 200

    def test_invalid_host_returns_404_not_403(self, client: TestClient, auth_token: str):
        """Verify invalid host returns 404, not 403"""
        response = client.get(
            "/api/files/nonexistent-host/list",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/"}
        )

        assert response.status_code == 404

    def test_unauthenticated_cannot_access_any_files(self, client: TestClient, created_host):
        """Verify unauthenticated users cannot access any files"""
        host_id = created_host["id"]

        response = client.get(
            f"/api/files/{host_id}/list",
            params={"path": "/"}
        )

        assert response.status_code == 401

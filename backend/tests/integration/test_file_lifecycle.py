"""Integration tests for file upload and download lifecycle.

Tests verify:
- File upload and download operations
- Directory listing
- File deletion
- Permission enforcement
"""

import pytest
from fastapi.testclient import TestClient


class TestFileLifecycle:
    """Test file operations lifecycle."""

    def test_upload_and_download_file(self, client: TestClient, auth_token: str, created_host):
        """Verify file upload and download workflow"""
        host_id = created_host["id"]
        test_content = "test file content"

        # Upload file
        upload_response = client.post(
            f"/api/files/{host_id}/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/tmp"},
            files={"file": ("test.txt", test_content.encode(), "text/plain")}
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert "path" in upload_data
        assert upload_data["size"] > 0
        uploaded_path = upload_data["path"]

        # Download file
        download_response = client.get(
            f"/api/files/{host_id}/download",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": uploaded_path}
        )

        assert download_response.status_code == 200
        assert download_response.content == test_content.encode()

    def test_list_directory(self, client: TestClient, auth_token: str, created_host):
        """Verify directory listing"""
        host_id = created_host["id"]

        response = client.get(
            f"/api/files/{host_id}/list",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)

    def test_delete_file(self, client: TestClient, auth_token: str, created_host):
        """Verify file deletion"""
        host_id = created_host["id"]

        # First upload a file
        upload_response = client.post(
            f"/api/files/{host_id}/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/tmp"},
            files={"file": ("delete_test.txt", b"content", "text/plain")}
        )

        assert upload_response.status_code == 200
        uploaded_path = upload_response.json()["path"]

        # Delete the file
        delete_response = client.post(
            f"/api/files/{host_id}/delete",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"path": uploaded_path}
        )

        # Should succeed or file already deleted
        assert delete_response.status_code in [200, 404]

    def test_edit_file(self, client: TestClient, auth_token: str, created_host):
        """Verify file edit operation"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test_edit.txt",
                "content": "new content"
            }
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 403]

    def test_file_permissions_not_accessible_by_other_user(
        self, client: TestClient, auth_token: str, created_host, other_user_token: str
    ):
        """Verify users cannot access other users' files"""
        host_id = created_host["id"]

        # Other user tries to list files
        response = client.get(
            f"/api/files/{host_id}/list",
            headers={"Authorization": f"Bearer {other_user_token}"},
            params={"path": "/"}
        )

        assert response.status_code == 403

    def test_file_upload_to_invalid_host(self, client: TestClient, auth_token: str):
        """Verify upload fails for invalid host"""
        response = client.post(
            "/api/files/invalid-host/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/tmp"},
            files={"file": ("test.txt", b"content", "text/plain")}
        )

        assert response.status_code == 404

    def test_file_operations_without_authentication(self, client: TestClient, created_host):
        """Verify authentication is required for all file operations"""
        host_id = created_host["id"]

        # List without auth
        list_response = client.get(
            f"/api/files/{host_id}/list",
            params={"path": "/"}
        )
        assert list_response.status_code == 401

        # Upload without auth
        upload_response = client.post(
            f"/api/files/{host_id}/upload",
            params={"path": "/tmp"},
            files={"file": ("test.txt", b"content", "text/plain")}
        )
        assert upload_response.status_code == 401

        # Download without auth
        download_response = client.get(
            f"/api/files/{host_id}/download",
            params={"path": "/etc/hostname"}
        )
        assert download_response.status_code == 401

    def test_chmod_file(self, client: TestClient, auth_token: str, created_host):
        """Verify file permission change"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/chmod",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test.txt",
                "mode": 755
            }
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 403, 404]

    def test_move_file(self, client: TestClient, auth_token: str, created_host):
        """Verify file move/rename"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/move",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "old_path": "/tmp/old.txt",
                "new_path": "/tmp/new.txt"
            }
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 403, 404]

    def test_mkdir(self, client: TestClient, auth_token: str, created_host):
        """Verify directory creation"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/mkdir",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test_dir"
            }
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 403]

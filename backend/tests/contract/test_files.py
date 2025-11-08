"""Contract tests for file endpoints.

Tests verify:
- GET /files/{host_id}/list: directory listing contract
- POST /files/{host_id}/upload: file upload contract
- GET /files/{host_id}/download: file download contract
- POST /files/{host_id}/edit: file edit contract
- POST /files/{host_id}/chmod: chmod contract
"""

import pytest
from fastapi.testclient import TestClient


class TestFileListContract:
    """T114: Contract test for GET /files/{host_id}/list"""

    def test_get_directory_listing(self, client: TestClient, auth_token: str, created_host):
        """Verify directory listing returns FileInfo with metadata"""
        host_id = created_host["id"]

        response = client.get(
            f"/api/files/{host_id}/list",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/home"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)
        # Each entry should have file metadata
        if data["entries"]:
            entry = data["entries"][0]
            assert "name" in entry
            assert "type" in entry  # file, directory, symlink
            assert "size" in entry
            assert "mode" in entry  # permissions
            assert "modified" in entry  # modification time
            assert "owner" in entry  # uid/gid

    def test_get_directory_listing_authentication_required(self, client: TestClient, created_host):
        """Verify authentication is required"""
        host_id = created_host["id"]

        response = client.get(f"/api/files/{host_id}/list", params={"path": "/home"})

        assert response.status_code == 401

    def test_get_directory_listing_invalid_host(self, client: TestClient, auth_token: str):
        """Verify invalid host_id returns 404"""
        response = client.get(
            "/api/files/invalid-host/list",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/home"}
        )

        assert response.status_code == 404


class TestFileUploadContract:
    """T115: Contract test for POST /files/{host_id}/upload"""

    def test_post_file_upload(self, client: TestClient, auth_token: str, created_host):
        """Verify file upload returns UploadResponse"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/tmp"},
            files={"file": ("test.txt", b"test content", "text/plain")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert "size" in data
        assert "message" in data

    def test_post_file_upload_authentication_required(self, client: TestClient, created_host):
        """Verify authentication is required"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/upload",
            params={"path": "/tmp"},
            files={"file": ("test.txt", b"test content", "text/plain")}
        )

        assert response.status_code == 401

    def test_post_file_upload_invalid_host(self, client: TestClient, auth_token: str):
        """Verify invalid host_id returns 404"""
        response = client.post(
            "/api/files/invalid-host/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/tmp"},
            files={"file": ("test.txt", b"test content", "text/plain")}
        )

        assert response.status_code == 404


class TestFileDownloadContract:
    """T116: Contract test for GET /files/{host_id}/download"""

    def test_get_file_download(self, client: TestClient, auth_token: str, created_host):
        """Verify file download returns file content"""
        host_id = created_host["id"]

        response = client.get(
            f"/api/files/{host_id}/download",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/etc/hostname"}
        )

        # Should return 200 with file content or 404 if file doesn't exist
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            # Content should be bytes
            assert isinstance(response.content, bytes)

    def test_get_file_download_authentication_required(self, client: TestClient, created_host):
        """Verify authentication is required"""
        host_id = created_host["id"]

        response = client.get(
            f"/api/files/{host_id}/download",
            params={"path": "/etc/hostname"}
        )

        assert response.status_code == 401

    def test_get_file_download_invalid_host(self, client: TestClient, auth_token: str):
        """Verify invalid host_id returns 404"""
        response = client.get(
            "/api/files/invalid-host/download",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"path": "/etc/hostname"}
        )

        assert response.status_code == 404


class TestFileEditContract:
    """T117: Contract test for POST /files/{host_id}/edit"""

    def test_post_file_edit(self, client: TestClient, auth_token: str, created_host):
        """Verify file edit returns FileContent"""
        host_id = created_host["id"]

        # First create or read a file
        response = client.post(
            f"/api/files/{host_id}/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test_edit.txt",
                "content": "updated content",
                "mode": "write"
            }
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 403, 404]
        if response.status_code == 200:
            data = response.json()
            assert "path" in data
            assert "content" in data

    def test_post_file_edit_authentication_required(self, client: TestClient, created_host):
        """Verify authentication is required"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/edit",
            json={
                "path": "/tmp/test.txt",
                "content": "content"
            }
        )

        assert response.status_code == 401

    def test_post_file_edit_invalid_host(self, client: TestClient, auth_token: str):
        """Verify invalid host_id returns 404"""
        response = client.post(
            "/api/files/invalid-host/edit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test.txt",
                "content": "content"
            }
        )

        assert response.status_code == 404


class TestFileChmodContract:
    """T118: Contract test for POST /files/{host_id}/chmod"""

    def test_post_file_chmod(self, client: TestClient, auth_token: str, created_host):
        """Verify chmod returns ChmodResponse"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/chmod",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test.txt",
                "mode": 644
            }
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 403, 404]
        if response.status_code == 200:
            data = response.json()
            assert "path" in data
            assert "mode" in data
            assert "message" in data

    def test_post_file_chmod_authentication_required(self, client: TestClient, created_host):
        """Verify authentication is required"""
        host_id = created_host["id"]

        response = client.post(
            f"/api/files/{host_id}/chmod",
            json={
                "path": "/tmp/test.txt",
                "mode": 644
            }
        )

        assert response.status_code == 401

    def test_post_file_chmod_invalid_host(self, client: TestClient, auth_token: str):
        """Verify invalid host_id returns 404"""
        response = client.post(
            "/api/files/invalid-host/chmod",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "path": "/tmp/test.txt",
                "mode": 644
            }
        )

        assert response.status_code == 404

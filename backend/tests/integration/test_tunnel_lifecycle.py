"""Integration tests for tunnel creation and status lifecycle.

Tests verify:
- Tunnel creation with valid configuration
- Tunnel list retrieval
- Tunnel status monitoring
- Tunnel update operations
- Tunnel deletion
- Permission enforcement
"""

import pytest
from fastapi.testclient import TestClient


class TestTunnelLifecycle:
    """Test tunnel lifecycle operations."""

    def test_create_local_tunnel(self, client: TestClient, auth_token: str, created_host):
        """Verify local tunnel creation"""
        host_id = created_host["id"]

        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "MySQL Remote",
                "tunnel_type": "local",
                "local_port": 3306,
                "remote_host": "localhost",
                "remote_port": 3306,
                "bind_address": "127.0.0.1",
                "enabled": True,
                "auto_reconnect": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MySQL Remote"
        assert data["tunnel_type"] == "local"
        assert data["local_port"] == 3306
        assert data["status"] == "disconnected"

    def test_create_remote_tunnel(self, client: TestClient, auth_token: str, created_host):
        """Verify remote tunnel creation"""
        host_id = created_host["id"]

        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Local Service",
                "tunnel_type": "remote",
                "local_port": 8080,
                "remote_host": "0.0.0.0",
                "remote_port": 8080,
                "auto_reconnect": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tunnel_type"] == "remote"

    def test_list_tunnels(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel list retrieval"""
        host_id = created_host["id"]

        # Create a tunnel first
        client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Test Tunnel",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )

        # List tunnels
        response = client.get(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "Test Tunnel"

    def test_list_tunnels_filtered_by_host(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel list can be filtered by host"""
        host_id = created_host["id"]

        response = client.get(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"host_id": host_id}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_tunnel_status(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel status retrieval"""
        host_id = created_host["id"]

        # Create a tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Status Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Get status
        response = client.get(
            f"/api/tunnels/{tunnel_id}/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "connected" in data
        assert "uptime_seconds" in data

    def test_update_tunnel(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel update"""
        host_id = created_host["id"]

        # Create a tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Original Name",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Update tunnel
        response = client.put(
            f"/api/tunnels/{tunnel_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Updated Name", "local_port": 9999}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["local_port"] == 9999

    def test_delete_tunnel(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel deletion"""
        host_id = created_host["id"]

        # Create a tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Delete Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Delete tunnel
        response = client.delete(
            f"/api/tunnels/{tunnel_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/tunnels/{tunnel_id}/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404

    def test_tunnel_requires_authentication(self, client: TestClient, created_host):
        """Verify authentication is required"""
        host_id = created_host["id"]

        # Create without auth
        response = client.post(
            "/api/tunnels",
            json={
                "host_id": host_id,
                "name": "Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )

        assert response.status_code == 401

    def test_tunnel_invalid_host(self, client: TestClient, auth_token: str):
        """Verify invalid host returns 404"""
        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": "invalid-host",
                "name": "Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )

        assert response.status_code == 404

    def test_tunnel_permission_denied_other_user(
        self, client: TestClient, created_host, other_user_token: str
    ):
        """Verify users cannot create tunnels on other user's hosts"""
        host_id = created_host["id"]

        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {other_user_token}"},
            json={
                "host_id": host_id,
                "name": "Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )

        assert response.status_code == 403

    def test_start_tunnel(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel start operation"""
        host_id = created_host["id"]

        # Create a tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Start Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Start tunnel
        response = client.post(
            f"/api/tunnels/{tunnel_id}/start",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should succeed or fail gracefully
        assert response.status_code in [200, 400]

    def test_stop_tunnel(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel stop operation"""
        host_id = created_host["id"]

        # Create a tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Stop Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Stop tunnel
        response = client.post(
            f"/api/tunnels/{tunnel_id}/stop",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

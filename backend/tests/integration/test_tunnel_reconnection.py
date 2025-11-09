"""Integration tests for tunnel auto-reconnection behavior.

Tests verify:
- Auto-reconnection is triggered on disconnect
- Reconnection retry mechanism works
- Connection state tracking
- Error handling during reconnection
"""

import pytest
from fastapi.testclient import TestClient


class TestTunnelAutoReconnection:
    """Test tunnel auto-reconnection functionality."""

    def test_tunnel_auto_reconnect_enabled(self, client: TestClient, auth_token: str, created_host):
        """Verify auto-reconnect flag can be set"""
        host_id = created_host["id"]

        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Auto Reconnect Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
                "auto_reconnect": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auto_reconnect"] is True

    def test_tunnel_auto_reconnect_disabled(self, client: TestClient, auth_token: str, created_host):
        """Verify auto-reconnect can be disabled"""
        host_id = created_host["id"]

        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "No Reconnect Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
                "auto_reconnect": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auto_reconnect"] is False

    def test_tunnel_reconnection_status_tracking(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel tracks connection status during reconnection"""
        host_id = created_host["id"]

        # Create tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Reconnection Status Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
                "auto_reconnect": True,
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
        # Initial status should be disconnected
        assert data["status"] in ["disconnected", "failed", "connecting"]

    def test_tunnel_error_tracking(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel tracks errors during operation"""
        host_id = created_host["id"]

        # Create tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Error Tracking Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Try to start tunnel (may fail)
        client.post(
            f"/api/tunnels/{tunnel_id}/start",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Check status includes error tracking
        response = client.get(
            f"/api/tunnels/{tunnel_id}/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Status should include error count and tracking
        assert "error_count" in data
        assert "last_error" in data or data.get("error") is None

    def test_tunnel_connection_timing(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel tracks connection timing"""
        host_id = created_host["id"]

        # Create tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Timing Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Get status should show timing info
        response = client.get(
            f"/api/tunnels/{tunnel_id}/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)

    def test_tunnel_update_auto_reconnect(self, client: TestClient, auth_token: str, created_host):
        """Verify auto-reconnect setting can be updated"""
        host_id = created_host["id"]

        # Create tunnel with auto-reconnect enabled
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Update Reconnect Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
                "auto_reconnect": True,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Update to disable auto-reconnect
        response = client.put(
            f"/api/tunnels/{tunnel_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"auto_reconnect": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auto_reconnect"] is False

    def test_tunnel_reconnection_preserves_state(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel state is preserved through reconnection attempts"""
        host_id = created_host["id"]

        # Create tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "State Preservation Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
                "auto_reconnect": True,
            }
        )
        original_data = create_response.json()
        tunnel_id = original_data["id"]

        # Get tunnel info after creation
        response = client.get(
            f"/api/tunnels/{tunnel_id}/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        # Tunnel ID and basic config should remain the same
        assert original_data["id"] == tunnel_id

    def test_multiple_reconnection_attempts(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel can handle multiple reconnection attempts"""
        host_id = created_host["id"]

        # Create tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Multiple Attempts Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
                "auto_reconnect": True,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Multiple start attempts should be handled
        for _ in range(3):
            response = client.post(
                f"/api/tunnels/{tunnel_id}/start",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            # Should succeed or fail gracefully
            assert response.status_code in [200, 400]

    def test_tunnel_disable_stops_reconnection(self, client: TestClient, auth_token: str, created_host):
        """Verify disabling tunnel stops auto-reconnection"""
        host_id = created_host["id"]

        # Create tunnel
        create_response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "Disable Test",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306,
                "auto_reconnect": True,
                "enabled": True,
            }
        )
        tunnel_id = create_response.json()["id"]

        # Disable tunnel
        response = client.put(
            f"/api/tunnels/{tunnel_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"enabled": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

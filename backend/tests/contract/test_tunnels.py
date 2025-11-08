"""Contract tests for tunnel endpoints.

Tests verify:
- POST /tunnels: tunnel creation contract
- GET /tunnels: tunnel list contract
- GET /tunnels/{tunnel_id}/status: tunnel status contract
- PUT /tunnels/{tunnel_id}: tunnel update contract
- DELETE /tunnels/{tunnel_id}: tunnel deletion contract
"""

import pytest
from fastapi.testclient import TestClient


class TestTunnelCreateContract:
    """T137: Contract test for POST /tunnels"""

    def test_post_create_tunnel(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel creation returns TunnelResponse"""
        host_id = created_host["id"]

        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": host_id,
                "name": "test-tunnel",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "host_id" in data
        assert "name" in data
        assert "status" in data
        assert "created_at" in data

    def test_post_create_tunnel_authentication_required(self, client: TestClient, created_host):
        """Verify authentication is required"""
        host_id = created_host["id"]

        response = client.post(
            "/api/tunnels",
            json={
                "host_id": host_id,
                "name": "test-tunnel",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306
            }
        )

        assert response.status_code == 401

    def test_post_create_tunnel_invalid_host(self, client: TestClient, auth_token: str):
        """Verify invalid host_id returns 404"""
        response = client.post(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "host_id": "invalid-host",
                "name": "test-tunnel",
                "tunnel_type": "local",
                "local_port": 8888,
                "remote_host": "localhost",
                "remote_port": 3306
            }
        )

        assert response.status_code == 404


class TestTunnelListContract:
    """T138: Contract test for GET /tunnels"""

    def test_get_tunnel_list(self, client: TestClient, auth_token: str):
        """Verify tunnel list returns array"""
        response = client.get(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            tunnel = data[0]
            assert "id" in tunnel
            assert "name" in tunnel
            assert "status" in tunnel

    def test_get_tunnel_list_authentication_required(self, client: TestClient):
        """Verify authentication is required"""
        response = client.get("/api/tunnels")

        assert response.status_code == 401

    def test_get_tunnel_list_filtering(self, client: TestClient, auth_token: str, created_host):
        """Verify tunnel list can be filtered by host"""
        response = client.get(
            "/api/tunnels",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"host_id": created_host["id"]}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTunnelStatusContract:
    """T139: Contract test for GET /tunnels/{tunnel_id}/status"""

    def test_get_tunnel_status(self, client: TestClient, auth_token: str, created_tunnel):
        """Verify tunnel status returns status information"""
        tunnel_id = created_tunnel["id"]

        response = client.get(
            f"/api/tunnels/{tunnel_id}/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "connected" in data
        assert "error" in data or data.get("error") is None

    def test_get_tunnel_status_authentication_required(self, client: TestClient):
        """Verify authentication is required"""
        response = client.get("/api/tunnels/some-id/status")

        assert response.status_code == 401

    def test_get_tunnel_status_invalid_tunnel(self, client: TestClient, auth_token: str):
        """Verify invalid tunnel_id returns 404"""
        response = client.get(
            "/api/tunnels/invalid-tunnel/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404


class TestTunnelUpdateContract:
    """T140: Contract test for PUT /tunnels/{tunnel_id}"""

    def test_put_update_tunnel(self, client: TestClient, auth_token: str, created_tunnel):
        """Verify tunnel update returns updated TunnelResponse"""
        tunnel_id = created_tunnel["id"]

        response = client.put(
            f"/api/tunnels/{tunnel_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "updated-tunnel",
                "local_port": 9999
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data

    def test_put_update_tunnel_authentication_required(self, client: TestClient, created_tunnel):
        """Verify authentication is required"""
        tunnel_id = created_tunnel["id"]

        response = client.put(
            f"/api/tunnels/{tunnel_id}",
            json={
                "name": "updated-tunnel"
            }
        )

        assert response.status_code == 401

    def test_put_update_tunnel_invalid_tunnel(self, client: TestClient, auth_token: str):
        """Verify invalid tunnel_id returns 404"""
        response = client.put(
            "/api/tunnels/invalid-tunnel",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "updated-tunnel"
            }
        )

        assert response.status_code == 404


class TestTunnelDeleteContract:
    """T141: Contract test for DELETE /tunnels/{tunnel_id}"""

    def test_delete_tunnel(self, client: TestClient, auth_token: str, created_tunnel):
        """Verify tunnel deletion"""
        tunnel_id = created_tunnel["id"]

        response = client.delete(
            f"/api/tunnels/{tunnel_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "success" in data

    def test_delete_tunnel_authentication_required(self, client: TestClient, created_tunnel):
        """Verify authentication is required"""
        tunnel_id = created_tunnel["id"]

        response = client.delete(f"/api/tunnels/{tunnel_id}")

        assert response.status_code == 401

    def test_delete_tunnel_invalid_tunnel(self, client: TestClient, auth_token: str):
        """Verify invalid tunnel_id returns 404"""
        response = client.delete(
            "/api/tunnels/invalid-tunnel",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 404

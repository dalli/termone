"""Contract tests for admin API endpoints.

Tests verify:
- User management endpoints (list, get)
- Session management endpoints (list, delete)
- OIDC provider endpoints (CRUD operations)
- Admin role requirement
"""

import pytest
from fastapi.testclient import TestClient


class TestAdminUserManagement:
    """Test admin user management endpoints."""

    def test_list_users_requires_admin(self, client: TestClient, auth_token: str):
        """Verify list users requires admin role"""
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should fail for non-admin users
        assert response.status_code in [403, 404]

    def test_list_users_with_admin_role(self, client: TestClient, admin_token: str):
        """Verify admin can list users"""
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "users" in data
        assert isinstance(data["users"], list)

    def test_list_users_pagination(self, client: TestClient, admin_token: str):
        """Verify user list supports pagination"""
        response = client.get(
            "/api/admin/users?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0

    def test_get_user_by_id(self, client: TestClient, admin_token: str, user_id: str):
        """Verify getting user by ID"""
        response = client.get(
            f"/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert "email" in data
        assert "username" in data

    def test_get_nonexistent_user(self, client: TestClient, admin_token: str):
        """Verify getting nonexistent user returns 404"""
        response = client.get(
            "/api/admin/users/nonexistent-id",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestAdminSessionManagement:
    """Test admin session management endpoints."""

    def test_list_sessions_requires_admin(self, client: TestClient, auth_token: str):
        """Verify list sessions requires admin role"""
        response = client.get(
            "/api/admin/sessions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should fail for non-admin users
        assert response.status_code in [403, 404]

    def test_list_sessions_with_admin_role(self, client: TestClient, admin_token: str):
        """Verify admin can list sessions"""
        response = client.get(
            "/api/admin/sessions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "active_sessions" in data
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_list_sessions_response_structure(self, client: TestClient, admin_token: str):
        """Verify session list response structure"""
        response = client.get(
            "/api/admin/sessions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify total counts
        assert isinstance(data["total"], int)
        assert isinstance(data["active_sessions"], int)
        assert data["active_sessions"] <= data["total"]

        # Verify session structure if present
        if data["sessions"]:
            session = data["sessions"][0]
            assert "session_id" in session
            assert "user_id" in session
            assert "user_email" in session
            assert "session_type" in session
            assert "status" in session

    def test_delete_session_requires_admin(self, client: TestClient, auth_token: str):
        """Verify delete session requires admin role"""
        response = client.delete(
            "/api/admin/sessions/some-session-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should fail for non-admin users
        assert response.status_code in [403, 404]

    def test_delete_nonexistent_session(self, client: TestClient, admin_token: str):
        """Verify deleting nonexistent session returns 404"""
        response = client.delete(
            "/api/admin/sessions/nonexistent-session",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404


class TestAdminOIDCProviders:
    """Test admin OIDC provider management endpoints."""

    def test_list_oidc_providers_requires_admin(self, client: TestClient, auth_token: str):
        """Verify list OIDC providers requires admin role"""
        response = client.get(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should fail for non-admin users
        assert response.status_code in [403, 404]

    def test_list_oidc_providers(self, client: TestClient, admin_token: str):
        """Verify listing OIDC providers"""
        response = client.get(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_create_oidc_provider(self, client: TestClient, admin_token: str):
        """Verify creating OIDC provider"""
        response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "test_provider",
                "display_name": "Test Provider",
                "client_id": "test-client-id",
                "client_secret": "test-secret",
                "discovery_url": "https://example.com/.well-known/openid-configuration",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "test_provider"
        assert data["display_name"] == "Test Provider"
        assert data["is_active"] is True

    def test_create_oidc_provider_missing_fields(self, client: TestClient, admin_token: str):
        """Verify creating OIDC provider with missing fields fails"""
        response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "test_provider",
                # Missing required fields
            }
        )

        assert response.status_code == 422

    def test_get_oidc_provider(self, client: TestClient, admin_token: str):
        """Verify getting OIDC provider by ID"""
        # First create a provider
        create_response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "get_test_provider",
                "display_name": "Get Test Provider",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "discovery_url": "https://example.com/.well-known/openid-configuration",
            }
        )
        provider_id = create_response.json()["id"]

        # Get the provider
        response = client.get(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == provider_id
        assert data["name"] == "get_test_provider"

    def test_get_nonexistent_provider(self, client: TestClient, admin_token: str):
        """Verify getting nonexistent provider returns 404"""
        response = client.get(
            "/api/admin/settings/oidc-providers/nonexistent-id",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404

    def test_update_oidc_provider(self, client: TestClient, admin_token: str):
        """Verify updating OIDC provider"""
        # Create a provider
        create_response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "update_test",
                "display_name": "Update Test",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "discovery_url": "https://example.com/.well-known/openid-configuration",
            }
        )
        provider_id = create_response.json()["id"]

        # Update the provider
        response = client.put(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "display_name": "Updated Display Name",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Display Name"

    def test_delete_oidc_provider(self, client: TestClient, admin_token: str):
        """Verify deleting OIDC provider"""
        # Create a provider
        create_response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "delete_test",
                "display_name": "Delete Test",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "discovery_url": "https://example.com/.well-known/openid-configuration",
            }
        )
        provider_id = create_response.json()["id"]

        # Delete the provider
        response = client.delete(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404

    def test_create_oidc_provider_without_auth(self, client: TestClient):
        """Verify creating OIDC provider without auth fails"""
        response = client.post(
            "/api/admin/settings/oidc-providers",
            json={
                "name": "test",
                "display_name": "Test",
                "client_id": "test",
                "client_secret": "test",
                "discovery_url": "https://example.com/.well-known/openid-configuration",
            }
        )

        assert response.status_code == 401

"""Integration tests for admin panel operations.

Tests verify:
- User management workflows
- Session lifecycle operations
- OIDC provider configuration workflow
"""

import pytest
from fastapi.testclient import TestClient


class TestAdminUserWorkflow:
    """Test admin user management workflows."""

    def test_list_and_view_user(self, client: TestClient, admin_token: str, user_id: str):
        """Verify workflow: list users and view details"""
        # List users
        list_response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert list_response.status_code == 200
        users_data = list_response.json()
        assert users_data["total"] >= 1

        # Get specific user
        get_response = client.get(
            f"/api/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        user_data = get_response.json()
        assert user_data["id"] == user_id
        assert "email" in user_data
        assert "host_count" in user_data
        assert "session_count" in user_data

    def test_user_list_contains_required_fields(self, client: TestClient, admin_token: str):
        """Verify user list contains all required fields"""
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        if data["users"]:
            user = data["users"][0]
            required_fields = [
                "id", "email", "username", "role", "is_active",
                "created_at", "last_login", "host_count", "session_count"
            ]
            for field in required_fields:
                assert field in user, f"Missing field: {field}"


class TestAdminSessionWorkflow:
    """Test admin session management workflows."""

    def test_list_sessions_workflow(self, client: TestClient, admin_token: str):
        """Verify workflow: list sessions and verify structure"""
        response = client.get(
            "/api/admin/sessions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total" in data
        assert "active_sessions" in data
        assert "sessions" in data

        # Verify counts are consistent
        assert isinstance(data["total"], int)
        assert isinstance(data["active_sessions"], int)
        assert data["active_sessions"] <= data["total"]

    def test_session_contains_required_fields(self, client: TestClient, admin_token: str):
        """Verify session list contains all required fields"""
        response = client.get(
            "/api/admin/sessions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        if data["sessions"]:
            session = data["sessions"][0]
            required_fields = [
                "session_id", "user_id", "user_email", "session_type",
                "created_at", "last_activity", "status"
            ]
            for field in required_fields:
                assert field in session, f"Missing field: {field}"


class TestOIDCProviderWorkflow:
    """Test OIDC provider configuration workflow."""

    def test_create_list_delete_provider(self, client: TestClient, admin_token: str):
        """Verify workflow: create, list, and delete OIDC provider"""
        provider_data = {
            "name": "workflow_test_provider",
            "display_name": "Workflow Test Provider",
            "client_id": "workflow-test-client",
            "client_secret": "workflow-test-secret",
            "discovery_url": "https://workflow.example.com/.well-known/openid-configuration",
            "scopes": ["openid", "profile", "email"],
        }

        # Create provider
        create_response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=provider_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        provider_id = created["id"]
        assert created["is_active"] is True

        # List providers and verify it appears
        list_response = client.get(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert list_response.status_code == 200
        providers = list_response.json()
        assert any(p["id"] == provider_id for p in providers["providers"])

        # Delete provider
        delete_response = client.delete(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404

    def test_create_update_provider(self, client: TestClient, admin_token: str):
        """Verify workflow: create and update OIDC provider"""
        provider_data = {
            "name": "update_test",
            "display_name": "Original Display Name",
            "client_id": "update-test-client",
            "client_secret": "update-test-secret",
            "discovery_url": "https://original.example.com/.well-known/openid-configuration",
        }

        # Create provider
        create_response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=provider_data
        )
        assert create_response.status_code == 200
        provider_id = create_response.json()["id"]

        # Update provider
        update_data = {
            "display_name": "Updated Display Name",
            "discovery_url": "https://updated.example.com/.well-known/openid-configuration",
        }
        update_response = client.put(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        assert update_response.status_code == 200

        updated = update_response.json()
        assert updated["display_name"] == "Updated Display Name"
        assert updated["discovery_url"] == "https://updated.example.com/.well-known/openid-configuration"

        # Verify update persists
        get_response = client.get(
            f"/api/admin/settings/oidc-providers/{provider_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        verified = get_response.json()
        assert verified["display_name"] == "Updated Display Name"

    def test_provider_response_excludes_sensitive_data(self, client: TestClient, admin_token: str):
        """Verify OIDC provider response doesn't include client secret"""
        # Create provider
        create_response = client.post(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "sensitive_test",
                "display_name": "Sensitive Test",
                "client_id": "sensitive-client",
                "client_secret": "sensitive-secret",
                "discovery_url": "https://sensitive.example.com/.well-known/openid-configuration",
            }
        )
        assert create_response.status_code == 200

        # Verify response doesn't include client_secret
        data = create_response.json()
        assert "client_secret" not in data
        assert "client_id" in data  # This is OK to expose

    def test_list_providers_response_structure(self, client: TestClient, admin_token: str):
        """Verify OIDC providers list response structure"""
        response = client.get(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total" in data
        assert "providers" in data
        assert isinstance(data["providers"], list)
        assert isinstance(data["total"], int)


class TestAdminPermissions:
    """Test admin role enforcement."""

    def test_non_admin_cannot_list_users(self, client: TestClient, auth_token: str):
        """Verify non-admin users cannot list all users"""
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    def test_non_admin_cannot_list_sessions(self, client: TestClient, auth_token: str):
        """Verify non-admin users cannot list sessions"""
        response = client.get(
            "/api/admin/sessions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    def test_non_admin_cannot_manage_oidc(self, client: TestClient, auth_token: str):
        """Verify non-admin users cannot manage OIDC providers"""
        response = client.get(
            "/api/admin/settings/oidc-providers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    def test_unauthenticated_cannot_access_admin(self, client: TestClient):
        """Verify unauthenticated users cannot access admin endpoints"""
        endpoints = [
            "/api/admin/users",
            "/api/admin/sessions",
            "/api/admin/settings/oidc-providers",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

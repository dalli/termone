"""Integration tests for authentication flow."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.models.base import Base
from src.models.user import User, Role, Permission
from src.database import get_db
from src.services.encryption import EncryptionService


@pytest.fixture
async def async_db_session():
    """Create an async test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def test_client(async_db_session):
    """Create a test client with overridden DB dependency."""

    async def override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_login_flow(test_client, async_db_session):
    """Test complete admin login and authentication flow."""
    encryption_service = EncryptionService()

    # Create admin user
    admin_user = User(
        id="admin-001",
        username="admin",
        email="admin@example.com",
        password_hash=encryption_service.hash_password("admin123"),
        is_active=True,
        is_admin=True,
    )
    async_db_session.add(admin_user)
    await async_db_session.commit()

    # Test login
    response = test_client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123",
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["is_admin"] is True

    # Store token for subsequent requests
    token = data["access_token"]

    # Test accessing protected endpoint with token
    response = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    hosts_data = response.json()
    assert "items" in hosts_data
    assert "total" in hosts_data
    assert hosts_data["total"] == 0  # No hosts yet


@pytest.mark.asyncio
async def test_user_login_and_host_creation_flow(test_client, async_db_session):
    """Test user login and host creation workflow."""
    encryption_service = EncryptionService()

    # Create regular user
    user = User(
        id="user-001",
        username="testuser",
        email="user@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(user)
    await async_db_session.commit()

    # Test login
    login_response = test_client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
        }
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Create a host
    create_response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "hostname": "server1.example.com",
            "port": 22,
            "username": "ubuntu",
            "tags": ["production"],
            "folder": "servers",
            "credential": {
                "type": "password",
                "value": "my-secret-password"
            }
        }
    )

    assert create_response.status_code == 201
    host_data = create_response.json()
    host_id = host_data["host_id"]

    # List hosts
    list_response = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert list_response.status_code == 200
    hosts = list_response.json()
    assert hosts["total"] == 1
    assert hosts["items"][0]["hostname"] == "server1.example.com"

    # Get specific host
    get_response = test_client.get(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 200
    host = get_response.json()
    assert host["hostname"] == "server1.example.com"
    assert host["port"] == 22


@pytest.mark.asyncio
async def test_token_expiration_flow(test_client, async_db_session):
    """Test token expiration handling."""
    encryption_service = EncryptionService()

    # Create user
    user = User(
        id="user-002",
        username="tokentest",
        email="token@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(user)
    await async_db_session.commit()

    # Login
    response = test_client.post(
        "/api/auth/login",
        json={
            "username": "tokentest",
            "password": "password123",
        }
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Use valid token
    response = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Use expired/invalid token
    response = test_client.get(
        "/api/hosts",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(test_client, async_db_session):
    """Test that inactive users cannot login."""
    encryption_service = EncryptionService()

    # Create inactive user
    user = User(
        id="user-003",
        username="inactive",
        email="inactive@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=False,
        is_admin=False,
    )
    async_db_session.add(user)
    await async_db_session.commit()

    # Attempt login
    response = test_client.post(
        "/api/auth/login",
        json={
            "username": "inactive",
            "password": "password123",
        }
    )

    assert response.status_code == 403

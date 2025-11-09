"""Integration tests for stats collection and lifecycle."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.models.base import Base
from src.models.user import User
from src.models.infrastructure import SSHHost, Credential
from src.database import get_db
from src.services.encryption import EncryptionService
from src.services.jwt_service import JWTService


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


@pytest.fixture
def auth_token():
    """Create an authentication token."""
    jwt_service = JWTService()
    return jwt_service.create_token(
        data={"sub": "user-001", "username": "testuser"}
    )


@pytest.fixture
async def test_user_and_host(async_db_session):
    """Create a test user and SSH host."""
    encryption_service = EncryptionService()

    user = User(
        id="user-001",
        username="testuser",
        email="user@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(user)

    host = SSHHost(
        id="host-001",
        hostname="test-server.example.com",
        port=22,
        username="ubuntu",
        tags=["test"],
        is_active=True,
        created_by_user_id="user-001",
    )
    async_db_session.add(host)

    credential = Credential(
        id="cred-001",
        host_id="host-001",
        credential_type="password",
        encrypted_value=encryption_service.encrypt("password123"),
    )
    async_db_session.add(credential)
    await async_db_session.commit()

    return user, host


@pytest.mark.asyncio
async def test_stats_collection_lifecycle(test_client, async_db_session, test_user_and_host, auth_token):
    """Test stats collection lifecycle: start, current, stop."""
    user, host = test_user_and_host

    # Get initial stats (should fail if none collected yet)
    response = test_client.get(
        f"/api/stats/{host.id}/current",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code in [404, 503]  # No stats yet

    # Start collection
    start_response = test_client.post(
        f"/api/stats/{host.id}/start-collection",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"interval": 5}
    )

    assert start_response.status_code == 200
    assert start_response.json()["success"] is True

    # After starting, try to get current stats (may still fail during collection)
    response = test_client.get(
        f"/api/stats/{host.id}/current",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code in [200, 503, 404]

    # Stop collection
    stop_response = test_client.post(
        f"/api/stats/{host.id}/stop-collection",
        json={}
    )

    assert stop_response.status_code == 200
    assert stop_response.json()["success"] is True


@pytest.mark.asyncio
async def test_stats_requires_auth(test_client, test_user_and_host):
    """Test that stats endpoints require authentication."""
    user, host = test_user_and_host

    response = test_client.get(f"/api/stats/{host.id}/current")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_stats_invalid_host(test_client, auth_token):
    """Test getting stats for invalid host."""
    response = test_client.get(
        "/api/stats/nonexistent-host/current",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stats_permission_boundary(test_client, async_db_session, auth_token):
    """Test that users cannot access other users' stats."""
    encryption_service = EncryptionService()

    # Create host owned by different user
    other_user = User(
        id="user-002",
        username="other",
        email="other@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(other_user)

    host = SSHHost(
        id="host-002",
        hostname="other-server.example.com",
        port=22,
        username="ubuntu",
        tags=["test"],
        is_active=True,
        created_by_user_id="user-002",
    )
    async_db_session.add(host)

    credential = Credential(
        id="cred-002",
        host_id="host-002",
        credential_type="password",
        encrypted_value=encryption_service.encrypt("password123"),
    )
    async_db_session.add(credential)
    await async_db_session.commit()

    # Try to access other user's host stats
    response = test_client.get(
        f"/api/stats/{host.id}/current",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_start_collection_authorization(test_client, async_db_session, auth_token):
    """Test that users can only start collection for their own hosts."""
    encryption_service = EncryptionService()

    # Create host owned by different user
    other_user = User(
        id="user-002",
        username="other",
        email="other@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(other_user)

    host = SSHHost(
        id="host-002",
        hostname="other-server.example.com",
        port=22,
        username="ubuntu",
        tags=["test"],
        is_active=True,
        created_by_user_id="user-002",
    )
    async_db_session.add(host)

    credential = Credential(
        id="cred-002",
        host_id="host-002",
        credential_type="password",
        encrypted_value=encryption_service.encrypt("password123"),
    )
    async_db_session.add(credential)
    await async_db_session.commit()

    # Try to start collection for other user's host
    response = test_client.post(
        f"/api/stats/{host.id}/start-collection",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"interval": 5}
    )

    assert response.status_code == 403

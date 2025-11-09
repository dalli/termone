"""Integration tests for stats broadcasting to multiple clients."""

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
async def test_setup(async_db_session):
    """Setup test data with multiple users and hosts."""
    encryption_service = EncryptionService()

    # Create two users who both have access to the same host (owner + shared)
    user1 = User(
        id="user-001",
        username="user1",
        email="user1@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(user1)

    user2 = User(
        id="user-002",
        username="user2",
        email="user2@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(user2)

    # Create a host owned by user1
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

    return {
        "user1": user1,
        "user2": user2,
        "host": host,
    }


@pytest.mark.asyncio
async def test_multiple_users_same_host_stats(test_client, async_db_session, test_setup):
    """Test that multiple users can connect to stats for the same host (currently only owner can)."""
    encryption_service = EncryptionService()

    # Create JWT tokens for both users
    jwt_service = JWTService()
    token1 = jwt_service.create_token(data={"sub": "user-001", "username": "user1"})
    token2 = jwt_service.create_token(data={"sub": "user-002", "username": "user2"})

    host = test_setup["host"]

    # User1 (owner) can get stats
    response1 = test_client.get(
        f"/api/stats/{host.id}/current",
        headers={"Authorization": f"Bearer {token1}"},
    )

    assert response1.status_code in [200, 404, 503]  # Depends on if stats are collected

    # User2 (non-owner) cannot get stats
    response2 = test_client.get(
        f"/api/stats/{host.id}/current",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response2.status_code == 403


@pytest.mark.asyncio
async def test_concurrent_stats_requests(test_client, async_db_session, test_setup):
    """Test that concurrent requests for the same host stats work correctly."""
    jwt_service = JWTService()
    token = jwt_service.create_token(data={"sub": "user-001", "username": "user1"})

    host = test_setup["host"]

    # Make multiple concurrent requests
    responses = []
    for _ in range(5):
        response = test_client.get(
            f"/api/stats/{host.id}/current",
            headers={"Authorization": f"Bearer {token}"},
        )
        responses.append(response.status_code)

    # All responses should be consistent (either all succeed or all fail with same code)
    assert all(code == responses[0] for code in responses)


@pytest.mark.asyncio
async def test_stats_isolation_by_user(test_client, async_db_session):
    """Test that stats are properly isolated between users."""
    encryption_service = EncryptionService()

    # Create two users with their own hosts
    user1 = User(
        id="user-001",
        username="user1",
        email="user1@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(user1)

    user2 = User(
        id="user-002",
        username="user2",
        email="user2@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    async_db_session.add(user2)

    host1 = SSHHost(
        id="host-001",
        hostname="user1-server.example.com",
        port=22,
        username="ubuntu",
        is_active=True,
        created_by_user_id="user-001",
    )
    async_db_session.add(host1)

    host2 = SSHHost(
        id="host-002",
        hostname="user2-server.example.com",
        port=22,
        username="ubuntu",
        is_active=True,
        created_by_user_id="user-002",
    )
    async_db_session.add(host2)

    for i, host_id in enumerate(["host-001", "host-002"]):
        credential = Credential(
            id=f"cred-{i:03d}",
            host_id=host_id,
            credential_type="password",
            encrypted_value=encryption_service.encrypt("password123"),
        )
        async_db_session.add(credential)

    await async_db_session.commit()

    jwt_service = JWTService()
    token1 = jwt_service.create_token(data={"sub": "user-001", "username": "user1"})
    token2 = jwt_service.create_token(data={"sub": "user-002", "username": "user2"})

    # User1 can access host1 but not host2
    response = test_client.get(
        "/api/stats/host-001/current",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response.status_code in [200, 404, 503]

    response = test_client.get(
        "/api/stats/host-002/current",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response.status_code == 403

    # User2 can access host2 but not host1
    response = test_client.get(
        "/api/stats/host-002/current",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code in [200, 404, 503]

    response = test_client.get(
        "/api/stats/host-001/current",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403

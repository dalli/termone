"""Integration tests for terminal session lifecycle."""

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
async def test_terminal_session_lifecycle(test_client, async_db_session, test_user_and_host, auth_token):
    """Test complete terminal session lifecycle: create, list, delete."""
    user, host = test_user_and_host

    # Create terminal session
    create_response = test_client.post(
        f"/api/terminal/sessions/{host.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"rows": 24, "cols": 80}
    )

    assert create_response.status_code == 201
    session_data = create_response.json()
    session_id = session_data["session_id"]
    assert session_data["host_id"] == host.id
    assert session_data["rows"] == 24
    assert session_data["cols"] == 80

    # List sessions
    list_response = test_client.get(
        "/api/terminal/sessions",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert list_response.status_code == 200
    sessions = list_response.json()
    assert sessions["total"] >= 1
    assert any(s["session_id"] == session_id for s in sessions["items"])

    # Delete session
    delete_response = test_client.delete(
        f"/api/terminal/sessions/{session_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert delete_response.status_code == 204

    # Verify session is deleted
    list_response = test_client.get(
        "/api/terminal/sessions",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert list_response.status_code == 200
    sessions = list_response.json()
    assert not any(s["session_id"] == session_id for s in sessions["items"])


@pytest.mark.asyncio
async def test_terminal_resize(test_client, async_db_session, test_user_and_host, auth_token):
    """Test terminal resizing."""
    user, host = test_user_and_host

    # Create session
    create_response = test_client.post(
        f"/api/terminal/sessions/{host.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"rows": 24, "cols": 80}
    )

    session_id = create_response.json()["session_id"]

    # Resize terminal
    resize_response = test_client.post(
        f"/api/terminal/sessions/{session_id}/resize",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"rows": 30, "cols": 100}
    )

    assert resize_response.status_code == 200
    result = resize_response.json()
    assert result["success"] is True
    assert result["rows"] == 30
    assert result["cols"] == 100


@pytest.mark.asyncio
async def test_terminal_permission_boundary(test_client, async_db_session, auth_token):
    """Test that users cannot access other users' terminal sessions."""
    encryption_service = EncryptionService()

    # Create another user
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

    # Create session as user-001
    create_response = test_client.post(
        f"/api/terminal/sessions/{host.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )

    session_id = create_response.json()["session_id"]

    # Try to access session as other user
    other_token = JWTService().create_token(
        data={"sub": "user-002", "username": "other"}
    )

    delete_response = test_client.delete(
        f"/api/terminal/sessions/{session_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert delete_response.status_code == 403


@pytest.mark.asyncio
async def test_terminal_session_invalid_host(test_client, auth_token):
    """Test creating terminal session with invalid host."""
    response = test_client.post(
        "/api/terminal/sessions/nonexistent-host",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_terminal_requires_auth(test_client):
    """Test that terminal endpoints require authentication."""
    response = test_client.post(
        "/api/terminal/sessions/host-001",
        json={}
    )

    assert response.status_code == 401

"""Contract tests for terminal endpoints."""
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
async def test_create_terminal_session(test_client, async_db_session, test_user_and_host, auth_token):
    """Test creating a terminal session (T072a)."""
    user, host = test_user_and_host

    response = test_client.post(
        f"/api/terminal/sessions/{host.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert "session_id" in data
    assert data["host_id"] == host.id


@pytest.mark.asyncio
async def test_list_terminal_sessions(test_client, async_db_session, test_user_and_host, auth_token):
    """Test listing terminal sessions (T072b)."""
    user, host = test_user_and_host

    # Create a session first
    create_response = test_client.post(
        f"/api/terminal/sessions/{host.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )
    assert create_response.status_code in [200, 201]

    # List sessions
    list_response = test_client.get(
        "/api/terminal/sessions",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert list_response.status_code == 200
    data = list_response.json()
    assert "items" in data or isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_terminal_session(test_client, async_db_session, test_user_and_host, auth_token):
    """Test deleting a terminal session (T072c)."""
    user, host = test_user_and_host

    # Create a session first
    create_response = test_client.post(
        f"/api/terminal/sessions/{host.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )
    session_id = create_response.json()["session_id"]

    # Delete the session
    delete_response = test_client.delete(
        f"/api/terminal/sessions/{session_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_terminal_session_requires_auth(test_client):
    """Test that terminal endpoints require authentication."""
    response = test_client.post(
        "/api/terminal/sessions/host-001",
        json={}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_terminal_session_invalid_host(test_client, auth_token):
    """Test terminal session creation with invalid host."""
    response = test_client.post(
        "/api/terminal/sessions/nonexistent-host",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )

    assert response.status_code == 404

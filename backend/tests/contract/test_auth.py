"""Contract tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio

from src.main import app
from src.models.base import Base
from src.models.user import User
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
async def test_login_success(test_client, async_db_session):
    """Test successful login returns JWT token."""
    # Create test user
    encryption_service = EncryptionService()
    test_user = User(
        id="test-user-001",
        username="admin",
        email="admin@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=True,
    )
    async_db_session.add(test_user)
    await async_db_session.commit()

    # Attempt login
    response = test_client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "password123",
        }
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_invalid_credentials(test_client, async_db_session):
    """Test login with invalid credentials returns 401."""
    # Create test user
    encryption_service = EncryptionService()
    test_user = User(
        id="test-user-002",
        username="admin",
        email="admin@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=True,
    )
    async_db_session.add(test_user)
    await async_db_session.commit()

    # Attempt login with wrong password
    response = test_client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "wrongpassword",
        }
    )

    # Verify response
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_login_user_not_found(test_client):
    """Test login with non-existent user returns 401."""
    response = test_client.post(
        "/api/auth/login",
        json={
            "username": "nonexistent",
            "password": "password123",
        }
    )

    # Verify response
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_login_inactive_user(test_client, async_db_session):
    """Test login with inactive user returns 403."""
    # Create inactive test user
    encryption_service = EncryptionService()
    test_user = User(
        id="test-user-003",
        username="inactive",
        email="inactive@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=False,
        is_admin=False,
    )
    async_db_session.add(test_user)
    await async_db_session.commit()

    # Attempt login
    response = test_client.post(
        "/api/auth/login",
        json={
            "username": "inactive",
            "password": "password123",
        }
    )

    # Verify response
    assert response.status_code == 403
    data = response.json()
    assert "error" in data or "detail" in data

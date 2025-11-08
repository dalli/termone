"""Integration tests for permission boundaries."""

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
async def two_users(async_db_session):
    """Create two test users."""
    encryption_service = EncryptionService()

    user1 = User(
        id="user-001",
        username="user1",
        email="user1@example.com",
        password_hash=encryption_service.hash_password("password1"),
        is_active=True,
        is_admin=False,
    )

    user2 = User(
        id="user-002",
        username="user2",
        email="user2@example.com",
        password_hash=encryption_service.hash_password("password2"),
        is_active=True,
        is_admin=False,
    )

    async_db_session.add(user1)
    async_db_session.add(user2)
    await async_db_session.commit()

    return user1, user2


@pytest.fixture
def create_token():
    """Create tokens for users."""
    jwt_service = JWTService()

    def _create_token(user_id: str, username: str) -> str:
        return jwt_service.create_token(
            data={"sub": user_id, "username": username}
        )

    return _create_token


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_hosts(
    test_client, async_db_session, two_users, create_token
):
    """Test that users cannot access other users' hosts."""
    user1, user2 = two_users
    token1 = create_token("user-001", "user1")
    token2 = create_token("user-002", "user2")

    # User 1 creates a host
    create_response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "hostname": "user1-server.example.com",
            "port": 22,
            "username": "ubuntu",
            "credential": {
                "type": "password",
                "value": "password"
            }
        }
    )

    assert create_response.status_code == 201
    host_id = create_response.json()["host_id"]

    # User 1 can access their own host
    user1_get = test_client.get(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert user1_get.status_code == 200

    # User 2 cannot access User 1's host
    user2_get = test_client.get(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert user2_get.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_hosts(
    test_client, async_db_session, two_users, create_token
):
    """Test that users cannot delete other users' hosts."""
    user1, user2 = two_users
    token1 = create_token("user-001", "user1")
    token2 = create_token("user-002", "user2")

    # User 1 creates a host
    create_response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "hostname": "protected-host.example.com",
            "port": 22,
            "username": "ubuntu",
            "credential": {
                "type": "password",
                "value": "password"
            }
        }
    )

    host_id = create_response.json()["host_id"]

    # User 2 cannot delete User 1's host
    delete_response = test_client.delete(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert delete_response.status_code == 403

    # Host should still exist for User 1
    get_response = test_client.get(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_hosts(
    test_client, async_db_session, two_users, create_token
):
    """Test that users cannot update other users' hosts."""
    user1, user2 = two_users
    token1 = create_token("user-001", "user1")
    token2 = create_token("user-002", "user2")

    # User 1 creates a host
    create_response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "hostname": "immutable-host.example.com",
            "port": 22,
            "username": "ubuntu",
            "tags": ["original"],
            "credential": {
                "type": "password",
                "value": "password"
            }
        }
    )

    host_id = create_response.json()["host_id"]

    # User 2 cannot update User 1's host
    update_response = test_client.put(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {token2}"},
        json={"tags": ["modified"]}
    )
    assert update_response.status_code == 403

    # Host should retain original data
    get_response = test_client.get(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert get_response.status_code == 200
    host = get_response.json()
    assert "original" in host["tags"]


@pytest.mark.asyncio
async def test_user_lists_only_their_own_hosts(
    test_client, async_db_session, two_users, create_token
):
    """Test that users only see their own hosts in list."""
    user1, user2 = two_users
    token1 = create_token("user-001", "user1")
    token2 = create_token("user-002", "user2")

    # User 1 creates 3 hosts
    for i in range(3):
        test_client.post(
            "/api/hosts",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "hostname": f"user1-server{i}.example.com",
                "port": 22,
                "username": "ubuntu",
                "credential": {
                    "type": "password",
                    "value": "password"
                }
            }
        )

    # User 2 creates 2 hosts
    for i in range(2):
        test_client.post(
            "/api/hosts",
            headers={"Authorization": f"Bearer {token2}"},
            json={
                "hostname": f"user2-server{i}.example.com",
                "port": 22,
                "username": "ubuntu",
                "credential": {
                    "type": "password",
                    "value": "password"
                }
            }
        )

    # User 1 sees only 3 hosts
    user1_list = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert user1_list.status_code == 200
    assert user1_list.json()["total"] == 3

    # User 2 sees only 2 hosts
    user2_list = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert user2_list.status_code == 200
    assert user2_list.json()["total"] == 2


@pytest.mark.asyncio
async def test_user_cannot_search_other_users_hosts(
    test_client, async_db_session, two_users, create_token
):
    """Test that search results are filtered by user."""
    user1, user2 = two_users
    token1 = create_token("user-001", "user1")
    token2 = create_token("user-002", "user2")

    # User 1 creates hosts with specific names
    test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "hostname": "unique-prod-server.example.com",
            "port": 22,
            "username": "ubuntu",
            "credential": {
                "type": "password",
                "value": "password"
            }
        }
    )

    # User 2 creates different hosts
    test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "hostname": "other-server.example.com",
            "port": 22,
            "username": "ubuntu",
            "credential": {
                "type": "password",
                "value": "password"
            }
        }
    )

    # User 2 searches for "prod"
    search_response = test_client.get(
        "/api/hosts/search",
        headers={"Authorization": f"Bearer {token2}"},
        params={"q": "prod"}
    )

    # User 2 should not find User 1's host
    assert search_response.status_code == 200
    assert search_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_user_cannot_deploy_key_to_other_users_hosts(
    test_client, async_db_session, two_users, create_token
):
    """Test that users cannot deploy keys to other users' hosts."""
    user1, user2 = two_users
    token1 = create_token("user-001", "user1")
    token2 = create_token("user-002", "user2")

    # User 1 creates a host
    create_response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "hostname": "secure-host.example.com",
            "port": 22,
            "username": "ubuntu",
            "credential": {
                "type": "password",
                "value": "password"
            }
        }
    )

    host_id = create_response.json()["host_id"]

    # User 2 cannot deploy key to User 1's host
    deploy_response = test_client.post(
        f"/api/hosts/{host_id}/deploy-public-key",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "public_key": "ssh-rsa AAAAB3NzaC1yc2E... user@host"
        }
    )

    assert deploy_response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_access_hosts(test_client):
    """Test that unauthenticated requests are denied."""
    # Request without token
    response = test_client.get("/api/hosts")
    assert response.status_code == 401

    # Request with invalid token
    response = test_client.get(
        "/api/hosts",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code in [401, 403]

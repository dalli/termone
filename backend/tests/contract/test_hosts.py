"""Contract tests for hosts API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import json

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
def auth_token(async_db_session):
    """Create an authenticated token."""
    jwt_service = JWTService()
    return jwt_service.create_token(
        data={"sub": "test-user-001", "username": "admin"}
    )


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
async def test_user(async_db_session):
    """Create a test user."""
    encryption_service = EncryptionService()
    user = User(
        id="test-user-001",
        username="admin",
        email="admin@example.com",
        password_hash=encryption_service.hash_password("password123"),
        is_active=True,
        is_admin=True,
    )
    async_db_session.add(user)
    await async_db_session.commit()
    return user


@pytest.mark.asyncio
async def test_create_host_with_password(test_client, async_db_session, test_user, auth_token):
    """Test creating a host with password credential."""
    response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "prod-server-01",
            "port": 22,
            "username": "ubuntu",
            "tags": ["production", "web"],
            "folder": "production",
            "credential": {
                "type": "password",
                "value": "my-secret-password"
            }
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["hostname"] == "prod-server-01"
    assert data["port"] == 22
    assert "host_id" in data
    # Verify credential is encrypted (should not return raw password)
    assert "credential" not in data


@pytest.mark.asyncio
async def test_create_host_with_ssh_key(test_client, async_db_session, test_user, auth_token):
    """Test creating a host with SSH key credential."""
    ssh_key = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUtbm9uZQAAAAgAAAAAAAAAEQAAABIAAAALCm5v
-----END OPENSSH PRIVATE KEY-----"""

    response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "dev-server-01",
            "port": 2222,
            "username": "deploy",
            "tags": ["development"],
            "folder": "development",
            "credential": {
                "type": "ssh_key",
                "value": ssh_key
            }
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["hostname"] == "dev-server-01"
    assert data["port"] == 2222
    assert "host_id" in data


@pytest.mark.asyncio
async def test_list_hosts(test_client, async_db_session, test_user, auth_token):
    """Test listing hosts with pagination."""
    # Create multiple hosts
    encryption_service = EncryptionService()
    for i in range(3):
        host = SSHHost(
            id=f"host-{i}",
            hostname=f"server-{i}.example.com",
            port=22,
            username="ubuntu",
            tags=["prod"] if i % 2 == 0 else ["dev"],
            folder="servers",
            is_active=True,
            created_by_user_id=test_user.id,
        )
        async_db_session.add(host)

        credential = Credential(
            id=f"cred-{i}",
            host_id=f"host-{i}",
            credential_type="password",
            encrypted_value=encryption_service.encrypt("password123"),
        )
        async_db_session.add(credential)

    await async_db_session.commit()

    # List hosts
    response = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"skip": 0, "limit": 10}
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_hosts_with_filter(test_client, async_db_session, test_user, auth_token):
    """Test listing hosts with tag filter."""
    encryption_service = EncryptionService()

    # Create hosts with different tags
    for i in range(2):
        host = SSHHost(
            id=f"host-{i}",
            hostname=f"prod-server-{i}.example.com",
            port=22,
            username="ubuntu",
            tags=["production"],
            folder="production",
            is_active=True,
            created_by_user_id=test_user.id,
        )
        async_db_session.add(host)

        credential = Credential(
            id=f"cred-prod-{i}",
            host_id=f"host-{i}",
            credential_type="password",
            encrypted_value=encryption_service.encrypt("password123"),
        )
        async_db_session.add(credential)

    # Create dev host
    dev_host = SSHHost(
        id="host-dev",
        hostname="dev-server.example.com",
        port=22,
        username="ubuntu",
        tags=["development"],
        folder="development",
        is_active=True,
        created_by_user_id=test_user.id,
    )
    async_db_session.add(dev_host)

    dev_credential = Credential(
        id="cred-dev",
        host_id="host-dev",
        credential_type="password",
        encrypted_value=encryption_service.encrypt("password123"),
    )
    async_db_session.add(dev_credential)
    await async_db_session.commit()

    # Filter by tag
    response = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"skip": 0, "limit": 10, "tags": "production"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("production" in item["tags"] for item in data["items"])


@pytest.mark.asyncio
async def test_get_host_by_id(test_client, async_db_session, test_user, auth_token):
    """Test retrieving a specific host."""
    encryption_service = EncryptionService()

    host = SSHHost(
        id="host-001",
        hostname="specific-server.example.com",
        port=22,
        username="ubuntu",
        tags=["production"],
        folder="production",
        is_active=True,
        created_by_user_id=test_user.id,
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

    response = test_client.get(
        "/api/hosts/host-001",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["host_id"] == "host-001"
    assert data["hostname"] == "specific-server.example.com"


@pytest.mark.asyncio
async def test_update_host(test_client, async_db_session, test_user, auth_token):
    """Test updating a host."""
    encryption_service = EncryptionService()

    host = SSHHost(
        id="host-002",
        hostname="old-hostname.example.com",
        port=22,
        username="ubuntu",
        tags=["production"],
        folder="production",
        is_active=True,
        created_by_user_id=test_user.id,
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

    response = test_client.put(
        "/api/hosts/host-002",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "new-hostname.example.com",
            "port": 2222,
            "tags": ["updated"],
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == "new-hostname.example.com"
    assert data["port"] == 2222


@pytest.mark.asyncio
async def test_delete_host(test_client, async_db_session, test_user, auth_token):
    """Test deleting a host."""
    encryption_service = EncryptionService()

    host = SSHHost(
        id="host-003",
        hostname="to-delete.example.com",
        port=22,
        username="ubuntu",
        tags=["temporary"],
        folder="temp",
        is_active=True,
        created_by_user_id=test_user.id,
    )
    async_db_session.add(host)

    credential = Credential(
        id="cred-003",
        host_id="host-003",
        credential_type="password",
        encrypted_value=encryption_service.encrypt("password123"),
    )
    async_db_session.add(credential)
    await async_db_session.commit()

    response = test_client.delete(
        "/api/hosts/host-003",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify host is deleted
    response = test_client.get(
        "/api/hosts/host-003",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deploy_public_key(test_client, async_db_session, test_user, auth_token):
    """Test deploying public key to host."""
    encryption_service = EncryptionService()

    host = SSHHost(
        id="host-004",
        hostname="deploy-key.example.com",
        port=22,
        username="ubuntu",
        tags=["production"],
        folder="production",
        is_active=True,
        created_by_user_id=test_user.id,
    )
    async_db_session.add(host)

    credential = Credential(
        id="cred-004",
        host_id="host-004",
        credential_type="password",
        encrypted_value=encryption_service.encrypt("password123"),
    )
    async_db_session.add(credential)
    await async_db_session.commit()

    public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDx... user@host"

    response = test_client.post(
        "/api/hosts/host-004/deploy-public-key",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"public_key": public_key}
    )

    # This should return 202 (Accepted) as it's an async operation
    assert response.status_code in [200, 202]
    data = response.json()
    assert "status" in data or "message" in data

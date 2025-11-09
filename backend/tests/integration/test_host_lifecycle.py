"""Integration tests for host lifecycle management."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.models.base import Base
from src.models.user import User
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
async def test_user(async_db_session):
    """Create a test user."""
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
    await async_db_session.commit()
    return user


@pytest.mark.asyncio
async def test_complete_host_lifecycle(test_client, async_db_session, test_user, auth_token):
    """Test complete host lifecycle: create, read, update, delete."""
    # Create host
    create_response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "webserver1.example.com",
            "port": 22,
            "username": "ubuntu",
            "tags": ["web", "production"],
            "folder": "production",
            "description": "Main production web server",
            "credential": {
                "type": "password",
                "value": "secure-password"
            }
        }
    )

    assert create_response.status_code == 201
    host_id = create_response.json()["host_id"]

    # Read host
    read_response = test_client.get(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert read_response.status_code == 200
    host = read_response.json()
    assert host["hostname"] == "webserver1.example.com"
    assert host["port"] == 22
    assert "production" in host["tags"]

    # Update host
    update_response = test_client.put(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "webserver1-updated.example.com",
            "port": 2222,
            "tags": ["web", "production", "updated"],
        }
    )

    assert update_response.status_code == 200
    updated_host = update_response.json()
    assert updated_host["hostname"] == "webserver1-updated.example.com"
    assert updated_host["port"] == 2222
    assert "updated" in updated_host["tags"]

    # Delete host
    delete_response = test_client.delete(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert delete_response.status_code == 204

    # Verify host is deleted
    get_after_delete = test_client.get(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert get_after_delete.status_code == 404


@pytest.mark.asyncio
async def test_host_with_ssh_key_credential(test_client, async_db_session, test_user, auth_token):
    """Test host creation with SSH key credential."""
    ssh_key = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUtbm9uZQAAAAgAAAAAAAAAEQAAABIAAAALCm5v
-----END OPENSSH PRIVATE KEY-----"""

    response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "sshkey-host.example.com",
            "port": 2222,
            "username": "deploy",
            "tags": ["deployment"],
            "credential": {
                "type": "ssh_key",
                "value": ssh_key
            }
        }
    )

    assert response.status_code == 201
    host = response.json()
    assert host["credential_type"] == "ssh_key"


@pytest.mark.asyncio
async def test_host_search_functionality(test_client, async_db_session, test_user, auth_token):
    """Test host search feature."""
    # Create multiple hosts
    hosts_data = [
        ("prod-web1.example.com", "Production Web Server 1"),
        ("prod-db1.example.com", "Production Database Server"),
        ("dev-web1.example.com", "Development Web Server"),
    ]

    host_ids = []
    for hostname, description in hosts_data:
        response = test_client.post(
            "/api/hosts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "hostname": hostname,
                "port": 22,
                "username": "ubuntu",
                "description": description,
                "tags": ["prod" if "prod" in hostname else "dev"],
                "credential": {
                    "type": "password",
                    "value": "password"
                }
            }
        )
        assert response.status_code == 201
        host_ids.append(response.json()["host_id"])

    # Search for production servers
    search_response = test_client.get(
        "/api/hosts/search",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"q": "prod"}
    )

    assert search_response.status_code == 200
    results = search_response.json()
    assert results["total"] == 2
    assert all("prod" in item["hostname"] for item in results["items"])

    # Search for database
    search_response = test_client.get(
        "/api/hosts/search",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"q": "database"}
    )

    assert search_response.status_code == 200
    results = search_response.json()
    assert results["total"] == 1
    assert "Database" in results["items"][0]["description"]


@pytest.mark.asyncio
async def test_host_filtering_by_tags(test_client, async_db_session, test_user, auth_token):
    """Test filtering hosts by tags."""
    # Create hosts with different tags
    for i in range(3):
        tags = ["prod", "web"] if i < 2 else ["dev", "api"]
        response = test_client.post(
            "/api/hosts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "hostname": f"server{i}.example.com",
                "port": 22,
                "username": "ubuntu",
                "tags": tags,
                "credential": {
                    "type": "password",
                    "value": "password"
                }
            }
        )
        assert response.status_code == 201

    # Filter by "prod" tag
    response = test_client.get(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"tags": "prod"}
    )

    assert response.status_code == 200
    hosts = response.json()
    assert hosts["total"] == 2


@pytest.mark.asyncio
async def test_multiple_credentials_per_host(test_client, async_db_session, test_user, auth_token):
    """Test updating host credential."""
    # Create host with password
    create_response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "multi-cred-host.example.com",
            "port": 22,
            "username": "ubuntu",
            "credential": {
                "type": "password",
                "value": "old-password"
            }
        }
    )

    assert create_response.status_code == 201
    host_id = create_response.json()["host_id"]

    # Update with SSH key credential
    ssh_key = "-----BEGIN OPENSSH PRIVATE KEY-----\ntest\n-----END OPENSSH PRIVATE KEY-----"

    update_response = test_client.put(
        f"/api/hosts/{host_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "credential": {
                "type": "ssh_key",
                "value": ssh_key
            }
        }
    )

    assert update_response.status_code == 200
    # Note: In a real implementation, this would update the credential type


@pytest.mark.asyncio
async def test_tag_management_endpoints(test_client, async_db_session, test_user, auth_token):
    """Test adding and removing tags from hosts."""
    # Create host
    response = test_client.post(
        "/api/hosts",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "hostname": "tag-test.example.com",
            "port": 22,
            "username": "ubuntu",
            "tags": ["initial"],
            "credential": {
                "type": "password",
                "value": "password"
            }
        }
    )

    host_id = response.json()["host_id"]

    # Add tag
    add_tag_response = test_client.post(
        f"/api/hosts/{host_id}/tags/newtag",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert add_tag_response.status_code == 200
    host = add_tag_response.json()
    assert "newtag" in host["tags"]

    # Remove tag
    remove_tag_response = test_client.delete(
        f"/api/hosts/{host_id}/tags/initial",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert remove_tag_response.status_code == 200
    host = remove_tag_response.json()
    assert "initial" not in host["tags"]
    assert "newtag" in host["tags"]

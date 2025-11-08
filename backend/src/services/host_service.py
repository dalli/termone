"""Host management service."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from src.models.infrastructure import SSHHost, Credential
from src.services.credential_service import CredentialService
from src.exceptions import ValidationException, NotFoundException, PermissionException


class HostService:
    """Service for managing SSH hosts."""

    def __init__(self, credential_service: Optional[CredentialService] = None):
        """Initialize host service."""
        self.credential_service = credential_service

    async def create_host(
        self,
        db: AsyncSession,
        hostname: str,
        port: int,
        username: str,
        user_id: str,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        description: Optional[str] = None,
        credential_type: Optional[str] = None,
        credential_value: Optional[str] = None,
    ) -> SSHHost:
        """
        Create a new SSH host.

        Args:
            db: Database session
            hostname: Host hostname or IP
            port: SSH port
            username: SSH username
            user_id: User creating the host
            tags: List of tags for organization
            folder: Folder for organization
            description: Host description
            credential_type: Type of credential
            credential_value: Encrypted credential value

        Returns:
            Created SSHHost object

        Raises:
            ValidationException: If host data is invalid
        """
        if not hostname or len(hostname.strip()) == 0:
            raise ValidationException(
                field="hostname",
                message="Hostname cannot be empty",
                code="EMPTY_HOSTNAME",
            )

        if not username or len(username.strip()) == 0:
            raise ValidationException(
                field="username",
                message="Username cannot be empty",
                code="EMPTY_USERNAME",
            )

        # Check for duplicate hostname/port combination for this user
        result = await db.execute(
            select(SSHHost).where(
                and_(
                    SSHHost.hostname == hostname.strip(),
                    SSHHost.port == port,
                    SSHHost.created_by_user_id == user_id,
                )
            )
        )
        if result.scalar_one_or_none():
            raise ValidationException(
                field="hostname",
                message=f"Host {hostname}:{port} already exists",
                code="DUPLICATE_HOST",
            )

        host = SSHHost(
            id=str(uuid4()),
            hostname=hostname.strip(),
            port=port,
            username=username.strip(),
            tags=tags or [],
            folder=folder.strip() if folder else None,
            description=description,
            is_active=True,
            created_by_user_id=user_id,
        )

        db.add(host)
        await db.commit()

        # Create credential if provided
        if credential_type and credential_value:
            if self.credential_service:
                await self.credential_service.create_credential(
                    db,
                    host.id,
                    credential_type,
                    credential_value,
                )

        await db.refresh(host)
        return host

    async def get_host(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: Optional[str] = None,
    ) -> SSHHost:
        """
        Retrieve a host by ID.

        Args:
            db: Database session
            host_id: Host ID
            user_id: Optional user ID for permission check

        Returns:
            SSHHost object

        Raises:
            NotFoundException: If host not found
            PermissionException: If user doesn't have access
        """
        result = await db.execute(
            select(SSHHost)
            .where(SSHHost.id == host_id)
            .options(selectinload(SSHHost.credentials))
        )
        host = result.scalar_one_or_none()

        if not host:
            raise NotFoundException(resource="Host", identifier=host_id)

        if user_id and host.created_by_user_id != user_id:
            raise PermissionException(
                resource="Host",
                action="read",
                reason="User does not own this host",
            )

        return host

    async def list_hosts(
        self,
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[SSHHost], int]:
        """
        List hosts for a user with filtering.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum records to return
            tags: Filter by tags
            folder: Filter by folder
            is_active: Filter by active status

        Returns:
            Tuple of (hosts list, total count)
        """
        filters = [SSHHost.created_by_user_id == user_id]

        if tags:
            # SQLite doesn't have native array operators, so we check in Python
            # For production, consider using PostgreSQL with proper array operations
            pass

        if folder:
            filters.append(SSHHost.folder == folder)

        if is_active is not None:
            filters.append(SSHHost.is_active == is_active)

        # Get total count
        count_result = await db.execute(
            select(func.count(SSHHost.id)).where(and_(*filters))
        )
        total = count_result.scalar()

        # Get paginated results
        query = select(SSHHost).where(and_(*filters)).offset(skip).limit(limit)
        result = await db.execute(query)
        hosts = result.scalars().all()

        # Filter by tags in Python (SQLite limitation)
        if tags:
            hosts = [
                host for host in hosts
                if any(tag.lower() in [t.lower() for t in host.tags] for tag in tags)
            ]

        return hosts, total

    async def search_hosts(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[SSHHost], int]:
        """
        Search hosts by hostname or IP.

        Args:
            db: Database session
            user_id: User ID
            query: Search query
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            Tuple of (matching hosts, total count)
        """
        search_pattern = f"%{query}%"

        filters = [
            SSHHost.created_by_user_id == user_id,
            or_(
                SSHHost.hostname.ilike(search_pattern),
                SSHHost.description.ilike(search_pattern),
            ),
        ]

        # Get total count
        count_result = await db.execute(
            select(func.count(SSHHost.id)).where(and_(*filters))
        )
        total = count_result.scalar()

        # Get paginated results
        query_result = await db.execute(
            select(SSHHost).where(and_(*filters)).offset(skip).limit(limit)
        )
        hosts = query_result.scalars().all()

        return hosts, total

    async def update_host(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
        **kwargs
    ) -> SSHHost:
        """
        Update a host.

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID for permission check
            **kwargs: Fields to update (hostname, port, username, tags, folder, etc.)

        Returns:
            Updated SSHHost object

        Raises:
            NotFoundException: If host not found
            PermissionException: If user doesn't have access
        """
        host = await self.get_host(db, host_id, user_id)

        allowed_fields = {
            "hostname", "port", "username", "tags", "folder",
            "description", "is_active",
        }

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field == "hostname":
                    setattr(host, field, value.strip())
                elif field == "folder":
                    setattr(host, field, value.strip() if value else None)
                elif field == "tags":
                    setattr(host, field, [tag.strip().lower() for tag in value] if value else [])
                else:
                    setattr(host, field, value)

        db.add(host)
        await db.commit()
        await db.refresh(host)

        return host

    async def delete_host(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete a host and its credentials.

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID for permission check

        Returns:
            True if deleted successfully

        Raises:
            NotFoundException: If host not found
            PermissionException: If user doesn't have access
        """
        host = await self.get_host(db, host_id, user_id)

        # Delete associated credentials
        if self.credential_service:
            await self.credential_service.delete_host_credentials(db, host_id)

        await db.delete(host)
        await db.commit()

        return True

    async def bulk_delete_hosts(
        self,
        db: AsyncSession,
        host_ids: List[str],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Delete multiple hosts.

        Args:
            db: Database session
            host_ids: List of host IDs to delete
            user_id: User ID for permission check

        Returns:
            Dictionary with success/failed counts and details
        """
        successful = 0
        failed = 0
        errors = []

        for host_id in host_ids:
            try:
                await self.delete_host(db, host_id, user_id)
                successful += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "host_id": host_id,
                    "error": str(e),
                })

        return {
            "successful": successful,
            "failed": failed,
            "total": len(host_ids),
            "errors": errors,
        }

    async def get_host_by_hostname(
        self,
        db: AsyncSession,
        hostname: str,
        user_id: str,
    ) -> Optional[SSHHost]:
        """
        Get a host by hostname for a specific user.

        Args:
            db: Database session
            hostname: Hostname to search for
            user_id: User ID

        Returns:
            SSHHost object or None if not found
        """
        result = await db.execute(
            select(SSHHost).where(
                and_(
                    SSHHost.hostname == hostname,
                    SSHHost.created_by_user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_host_count(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> int:
        """
        Get the number of hosts owned by a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of hosts
        """
        result = await db.execute(
            select(func.count(SSHHost.id)).where(
                SSHHost.created_by_user_id == user_id
            )
        )
        return result.scalar() or 0

    async def deactivate_host(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
    ) -> SSHHost:
        """
        Deactivate a host (soft delete).

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID for permission check

        Returns:
            Updated SSHHost object
        """
        return await self.update_host(db, host_id, user_id, is_active=False)

    async def activate_host(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
    ) -> SSHHost:
        """
        Activate a host.

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID for permission check

        Returns:
            Updated SSHHost object
        """
        return await self.update_host(db, host_id, user_id, is_active=True)

    async def add_tag_to_host(
        self,
        db: AsyncSession,
        host_id: str,
        tag: str,
        user_id: str,
    ) -> SSHHost:
        """
        Add a tag to a host.

        Args:
            db: Database session
            host_id: Host ID
            tag: Tag to add
            user_id: User ID for permission check

        Returns:
            Updated SSHHost object
        """
        host = await self.get_host(db, host_id, user_id)

        tag_lower = tag.strip().lower()
        if tag_lower not in [t.lower() for t in host.tags]:
            host.tags.append(tag_lower)

        db.add(host)
        await db.commit()
        await db.refresh(host)

        return host

    async def remove_tag_from_host(
        self,
        db: AsyncSession,
        host_id: str,
        tag: str,
        user_id: str,
    ) -> SSHHost:
        """
        Remove a tag from a host.

        Args:
            db: Database session
            host_id: Host ID
            tag: Tag to remove
            user_id: User ID for permission check

        Returns:
            Updated SSHHost object
        """
        host = await self.get_host(db, host_id, user_id)

        tag_lower = tag.strip().lower()
        host.tags = [t for t in host.tags if t.lower() != tag_lower]

        db.add(host)
        await db.commit()
        await db.refresh(host)

        return host

"""Audit logging service for tracking user actions."""

from typing import Optional, Any, Dict
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog


class AuditService:
    """Service for logging audit events."""

    async def log_action(
        self,
        db: AsyncSession,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            db: Database session
            user_id: User performing the action
            action: Action performed (create, update, delete, read, etc.)
            resource_type: Type of resource (host, credential, etc.)
            resource_id: ID of the resource
            details: Additional details about the action
            ip_address: IP address of the user
            user_agent: User agent string
            status: Status of the action (success, failure)
            error_message: Error message if action failed

        Returns:
            Created AuditLog object
        """
        audit_log = AuditLog(
            id=str(uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )

        db.add(audit_log)
        await db.commit()

        return audit_log

    async def log_host_created(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: str,
        hostname: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log host creation.

        Args:
            db: Database session
            user_id: User who created the host
            host_id: ID of the created host
            hostname: Hostname of the host
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created AuditLog object
        """
        return await self.log_action(
            db,
            user_id,
            action="create",
            resource_type="host",
            resource_id=host_id,
            details={"hostname": hostname},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_host_updated(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: str,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log host update.

        Args:
            db: Database session
            user_id: User who updated the host
            host_id: ID of the updated host
            changes: Dictionary of changed fields
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created AuditLog object
        """
        return await self.log_action(
            db,
            user_id,
            action="update",
            resource_type="host",
            resource_id=host_id,
            details={"changes": changes},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_host_deleted(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: str,
        hostname: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log host deletion.

        Args:
            db: Database session
            user_id: User who deleted the host
            host_id: ID of the deleted host
            hostname: Hostname of the host
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created AuditLog object
        """
        return await self.log_action(
            db,
            user_id,
            action="delete",
            resource_type="host",
            resource_id=host_id,
            details={"hostname": hostname},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_host_accessed(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: str,
        hostname: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log host access.

        Args:
            db: Database session
            user_id: User accessing the host
            host_id: ID of the accessed host
            hostname: Hostname of the host
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created AuditLog object
        """
        return await self.log_action(
            db,
            user_id,
            action="access",
            resource_type="host",
            resource_id=host_id,
            details={"hostname": hostname},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_credential_created(
        self,
        db: AsyncSession,
        user_id: str,
        credential_id: str,
        host_id: str,
        credential_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log credential creation.

        Args:
            db: Database session
            user_id: User who created the credential
            credential_id: ID of the credential
            host_id: ID of the host
            credential_type: Type of credential
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created AuditLog object
        """
        return await self.log_action(
            db,
            user_id,
            action="create",
            resource_type="credential",
            resource_id=credential_id,
            details={"host_id": host_id, "type": credential_type},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_public_key_deployment(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: str,
        deployment_status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        Log public key deployment.

        Args:
            db: Database session
            user_id: User deploying the key
            host_id: ID of the host
            deployment_status: Status of deployment
            ip_address: IP address of the user
            user_agent: User agent string
            error_message: Error message if deployment failed

        Returns:
            Created AuditLog object
        """
        return await self.log_action(
            db,
            user_id,
            action="deploy_public_key",
            resource_type="host",
            resource_id=host_id,
            details={},
            ip_address=ip_address,
            user_agent=user_agent,
            status=deployment_status,
            error_message=error_message,
        )

    async def log_search(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        result_count: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Log host search.

        Args:
            db: Database session
            user_id: User performing search
            query: Search query
            result_count: Number of results found
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created AuditLog object
        """
        return await self.log_action(
            db,
            user_id,
            action="search",
            resource_type="host",
            resource_id="bulk",
            details={"query": query, "result_count": result_count},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def get_user_audit_log(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 100,
    ) -> list:
        """
        Get audit log for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return

        Returns:
            List of AuditLog objects
        """
        from sqlalchemy import select, desc

        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_resource_audit_log(
        self,
        db: AsyncSession,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> list:
        """
        Get audit log for a specific resource.

        Args:
            db: Database session
            resource_type: Type of resource
            resource_id: ID of the resource
            limit: Maximum number of records to return

        Returns:
            List of AuditLog objects
        """
        from sqlalchemy import select, desc

        result = await db.execute(
            select(AuditLog)
            .where(
                (AuditLog.resource_type == resource_type) &
                (AuditLog.resource_id == resource_id)
            )
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        return result.scalars().all()

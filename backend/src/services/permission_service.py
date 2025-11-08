"""Permission checking service for RBAC."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.user import User
from src.models.infrastructure import SSHHost
from src.exceptions import AuthorizationException, PermissionException, NotFoundException


class PermissionService:
    """Service for checking user permissions."""

    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user has permission for resource action.

        Args:
            user_id: User ID
            resource: Resource type (e.g., "host", "file")
            action: Action (e.g., "read", "write")
            db: Database session

        Returns:
            True if user has permission, raises exception otherwise
        """
        # Get user with roles and permissions
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise AuthorizationException("User not found")

        # Check if user is admin (has all permissions)
        if user.is_admin:
            return True

        # Check roles for permission
        for role in user.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True

        raise AuthorizationException(f"User lacks permission for {resource}:{action}")

    async def check_admin(self, user_id: str, db: AsyncSession) -> bool:
        """Check if user is admin."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_admin:
            raise AuthorizationException("Admin access required")

        return True

    async def check_host_access(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: str,
        action: str = "read",
    ) -> bool:
        """
        Check if user has access to a specific host.

        Args:
            db: Database session
            user_id: User ID
            host_id: Host ID
            action: Action (read, write, delete)

        Returns:
            True if user has access, raises exception otherwise

        Raises:
            NotFoundException: If host not found
            PermissionException: If user doesn't have access
        """
        # Get the host
        stmt = select(SSHHost).where(SSHHost.id == host_id)
        result = await db.execute(stmt)
        host = result.scalar_one_or_none()

        if not host:
            raise NotFoundException(resource="Host", identifier=host_id)

        # Check if user owns the host or is admin
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            raise NotFoundException(resource="User", identifier=user_id)

        # Admin can access any host
        if user.is_admin:
            return True

        # User must own the host
        if host.created_by_user_id != user_id:
            raise PermissionException(
                resource="Host",
                action=action,
                reason="User does not own this host",
            )

        return True


def get_permission_service() -> PermissionService:
    """Get permission service instance."""
    return PermissionService()

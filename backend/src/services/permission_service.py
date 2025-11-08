"""Permission checking service for RBAC."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.user import User
from src.exceptions import AuthorizationException


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


def get_permission_service() -> PermissionService:
    """Get permission service instance."""
    return PermissionService()

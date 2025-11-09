"""Admin service for managing users, sessions, and OIDC providers."""

from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models.user import User
from src.models.infrastructure import SSHHost as Host
from src.schemas.admin import (
    UserListItem,
    UserListResponse,
    SessionInfo,
    SessionListResponse,
    OIDCProviderConfig,
    OIDCProviderResponse,
    OIDCProviderCreateRequest,
    OIDCProviderUpdateRequest,
    OIDCProviderListResponse,
)


class AdminService:
    """Service for admin operations."""

    def __init__(self, db_session: AsyncSession):
        """Initialize admin service."""
        self.db = db_session
        # In-memory storage for sessions (would be from backend session store)
        self._active_sessions: Dict[str, SessionInfo] = {}

    async def list_users(
        self, skip: int = 0, limit: int = 50
    ) -> UserListResponse:
        """List all users with their metadata.

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            UserListResponse with user list and total count
        """
        # Get total user count
        total_result = await self.db.execute(
            select(func.count(User.id))
        )
        total = total_result.scalar() or 0

        # Get users
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        users = result.scalars().all()

        # Build user list items
        user_items = []
        for user in users:
            # Count user's hosts
            hosts_result = await self.db.execute(
                select(func.count(Host.id)).where(Host.user_id == user.id)
            )
            host_count = hosts_result.scalar() or 0

            # Count user's active sessions
            session_count = sum(
                1 for s in self._active_sessions.values()
                if s.user_id == user.id
            )

            user_items.append(
                UserListItem(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    created_at=user.created_at,
                    last_login=user.last_login,
                    is_active=user.is_active,
                    role=user.role,
                    host_count=host_count,
                    session_count=session_count,
                )
            )

        return UserListResponse(total=total, users=user_items)

    async def get_user(self, user_id: str) -> Optional[UserListItem]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            UserListItem or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            return None

        # Count user's hosts
        hosts_result = await self.db.execute(
            select(func.count(Host.id)).where(Host.user_id == user.id)
        )
        host_count = hosts_result.scalar() or 0

        # Count user's active sessions
        session_count = sum(
            1 for s in self._active_sessions.values()
            if s.user_id == user.id
        )

        return UserListItem(
            id=user.id,
            email=user.email,
            username=user.username,
            created_at=user.created_at,
            last_login=user.last_login,
            is_active=user.is_active,
            role=user.role,
            host_count=host_count,
            session_count=session_count,
        )

    def list_sessions(self) -> SessionListResponse:
        """List all active sessions.

        Returns:
            SessionListResponse with session list
        """
        sessions = list(self._active_sessions.values())
        active_count = sum(1 for s in sessions if s.status == "active")

        return SessionListResponse(
            total=len(sessions),
            active_sessions=active_count,
            sessions=sessions,
        )

    def register_session(
        self,
        session_id: str,
        user_id: str,
        user_email: str,
        host_id: Optional[str] = None,
        host_name: Optional[str] = None,
        session_type: str = "general",
    ) -> None:
        """Register a new session.

        Args:
            session_id: Unique session ID
            user_id: User ID
            user_email: User email
            host_id: Optional host ID
            host_name: Optional host name
            session_type: Type of session
        """
        self._active_sessions[session_id] = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            user_email=user_email,
            host_id=host_id,
            host_name=host_name,
            session_type=session_type,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status="active",
        )

    def unregister_session(self, session_id: str) -> bool:
        """Unregister a session.

        Args:
            session_id: Session ID to remove

        Returns:
            True if session was removed, False if not found
        """
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            return True
        return False

    def update_session_activity(self, session_id: str) -> bool:
        """Update last activity timestamp for a session.

        Args:
            session_id: Session ID

        Returns:
            True if updated, False if not found
        """
        if session_id in self._active_sessions:
            self._active_sessions[session_id].last_activity = datetime.utcnow()
            return True
        return False

    async def create_oidc_provider(
        self, req: OIDCProviderCreateRequest
    ) -> OIDCProviderResponse:
        """Create a new OIDC provider.

        Args:
            req: Provider creation request

        Returns:
            Created provider response
        """
        # In a real implementation, this would save to database
        # For now, we'll store in memory with a simple ID
        provider_id = f"oidc_{datetime.utcnow().timestamp()}"

        provider = OIDCProviderConfig(
            id=provider_id,
            name=req.name,
            display_name=req.display_name,
            client_id=req.client_id,
            client_secret=req.client_secret,
            discovery_url=req.discovery_url,
            scopes=req.scopes,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Store in memory (would be database in production)
        if not hasattr(self, "_oidc_providers"):
            self._oidc_providers = {}
        self._oidc_providers[provider_id] = provider

        return OIDCProviderResponse(
            id=provider.id,
            name=provider.name,
            display_name=provider.display_name,
            client_id=provider.client_id,
            discovery_url=provider.discovery_url,
            scopes=provider.scopes,
            is_active=provider.is_active,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )

    async def list_oidc_providers(self) -> OIDCProviderListResponse:
        """List all OIDC providers.

        Returns:
            List of providers
        """
        if not hasattr(self, "_oidc_providers"):
            self._oidc_providers = {}

        providers = list(self._oidc_providers.values())
        responses = [
            OIDCProviderResponse(
                id=p.id,
                name=p.name,
                display_name=p.display_name,
                client_id=p.client_id,
                discovery_url=p.discovery_url,
                scopes=p.scopes,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in providers
        ]

        return OIDCProviderListResponse(
            total=len(responses), providers=responses
        )

    async def get_oidc_provider(self, provider_id: str) -> Optional[OIDCProviderResponse]:
        """Get OIDC provider by ID.

        Args:
            provider_id: Provider ID

        Returns:
            Provider or None if not found
        """
        if not hasattr(self, "_oidc_providers"):
            self._oidc_providers = {}

        provider = self._oidc_providers.get(provider_id)
        if not provider:
            return None

        return OIDCProviderResponse(
            id=provider.id,
            name=provider.name,
            display_name=provider.display_name,
            client_id=provider.client_id,
            discovery_url=provider.discovery_url,
            scopes=provider.scopes,
            is_active=provider.is_active,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )

    async def update_oidc_provider(
        self, provider_id: str, req: OIDCProviderUpdateRequest
    ) -> Optional[OIDCProviderResponse]:
        """Update OIDC provider.

        Args:
            provider_id: Provider ID
            req: Update request

        Returns:
            Updated provider or None if not found
        """
        if not hasattr(self, "_oidc_providers"):
            self._oidc_providers = {}

        provider = self._oidc_providers.get(provider_id)
        if not provider:
            return None

        # Update fields if provided
        if req.display_name:
            provider.display_name = req.display_name
        if req.client_id:
            provider.client_id = req.client_id
        if req.client_secret:
            provider.client_secret = req.client_secret
        if req.discovery_url:
            provider.discovery_url = req.discovery_url
        if req.scopes is not None:
            provider.scopes = req.scopes
        if req.is_active is not None:
            provider.is_active = req.is_active

        provider.updated_at = datetime.utcnow()

        return OIDCProviderResponse(
            id=provider.id,
            name=provider.name,
            display_name=provider.display_name,
            client_id=provider.client_id,
            discovery_url=provider.discovery_url,
            scopes=provider.scopes,
            is_active=provider.is_active,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )

    async def delete_oidc_provider(self, provider_id: str) -> bool:
        """Delete OIDC provider.

        Args:
            provider_id: Provider ID

        Returns:
            True if deleted, False if not found
        """
        if not hasattr(self, "_oidc_providers"):
            self._oidc_providers = {}

        if provider_id in self._oidc_providers:
            del self._oidc_providers[provider_id]
            return True
        return False

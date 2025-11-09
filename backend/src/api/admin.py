"""Admin API endpoints for user, session, and OIDC provider management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.models.user import User
from src.services.admin_service import AdminService
from src.schemas.admin import (
    UserListResponse,
    SessionListResponse,
    OIDCProviderCreateRequest,
    OIDCProviderUpdateRequest,
    OIDCProviderListResponse,
    OIDCProviderResponse,
)
from src.core.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    """Get admin service instance."""
    return AdminService(db)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# User Management Endpoints

@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """List all users.

    Returns:
        UserListResponse: List of users with metadata
    """
    result = await admin_service.list_users(skip=skip, limit=limit)
    return result


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get user by ID.

    Args:
        user_id: User ID

    Returns:
        User details
    """
    user = await admin_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


# Session Management Endpoints

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """List all active sessions.

    Returns:
        SessionListResponse: List of active sessions
    """
    result = admin_service.list_sessions()
    return result


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Terminate a session.

    Args:
        session_id: Session ID to terminate

    Returns:
        Confirmation message
    """
    removed = admin_service.unregister_session(session_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Audit log
    print(f"[AUDIT] Admin {current_user.id} terminated session {session_id}")

    return {"message": "Session terminated", "session_id": session_id}


# OIDC Provider Endpoints

@router.post("/settings/oidc-providers", response_model=OIDCProviderResponse)
async def create_oidc_provider(
    req: OIDCProviderCreateRequest,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Create a new OIDC provider.

    Args:
        req: Provider creation request

    Returns:
        Created provider
    """
    provider = await admin_service.create_oidc_provider(req)

    # Audit log
    print(f"[AUDIT] Admin {current_user.id} created OIDC provider {req.name}")

    return provider


@router.get("/settings/oidc-providers", response_model=OIDCProviderListResponse)
async def list_oidc_providers(
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """List all OIDC providers.

    Returns:
        List of OIDC providers
    """
    result = await admin_service.list_oidc_providers()
    return result


@router.get("/settings/oidc-providers/{provider_id}", response_model=OIDCProviderResponse)
async def get_oidc_provider(
    provider_id: str,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get OIDC provider by ID.

    Args:
        provider_id: Provider ID

    Returns:
        Provider details
    """
    provider = await admin_service.get_oidc_provider(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    return provider


@router.put("/settings/oidc-providers/{provider_id}", response_model=OIDCProviderResponse)
async def update_oidc_provider(
    provider_id: str,
    req: OIDCProviderUpdateRequest,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Update OIDC provider.

    Args:
        provider_id: Provider ID
        req: Update request

    Returns:
        Updated provider
    """
    provider = await admin_service.update_oidc_provider(provider_id, req)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    # Audit log
    print(f"[AUDIT] Admin {current_user.id} updated OIDC provider {provider_id}")

    return provider


@router.delete("/settings/oidc-providers/{provider_id}")
async def delete_oidc_provider(
    provider_id: str,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Delete OIDC provider.

    Args:
        provider_id: Provider ID

    Returns:
        Confirmation message
    """
    deleted = await admin_service.delete_oidc_provider(provider_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    # Audit log
    print(f"[AUDIT] Admin {current_user.id} deleted OIDC provider {provider_id}")

    return {"message": "Provider deleted", "provider_id": provider_id}

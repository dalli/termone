"""Tunnel management API endpoints.

Provides SSH port forwarding management:
- POST /tunnels: Create tunnel
- GET /tunnels: List tunnels
- GET /tunnels/{tunnel_id}/status: Get tunnel status
- PUT /tunnels/{tunnel_id}: Update tunnel
- DELETE /tunnels/{tunnel_id}: Delete tunnel
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.models import User
from src.schemas.tunnels import (
    TunnelCreate,
    TunnelUpdate,
    TunnelResponse,
    TunnelListResponse,
    TunnelStatusInfo,
)
from src.services.audit_service import AuditService
from src.services.tunnel_service import TunnelService
from src.services.tunnel_manager import TunnelManager
from src.services.host_service import HostService
from src.services.credential_service import CredentialService

router = APIRouter(prefix="/tunnels", tags=["tunnels"])

# Service instances (initialized at startup)
from src.services.encryption import get_encryption_service

encryption_service = get_encryption_service()
credential_service = CredentialService(encryption_service)
tunnel_service = TunnelService(credential_service)
tunnel_manager = TunnelManager(tunnel_service)
host_service = HostService()
audit_service = AuditService()


@router.post("", response_model=TunnelResponse)
async def create_tunnel(
    request: TunnelCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create new SSH tunnel.

    Args:
        request: Tunnel creation request
        db: Database session
        user: Authenticated user

    Returns:
        TunnelResponse with tunnel details

    Raises:
        404: Host not found
        403: User does not have access to host
    """
    try:
        # Verify host exists and user owns it
        host = await host_service.get_host(db, request.host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")

        if host.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create tunnel
        tunnel = await tunnel_service.create_tunnel(db, user.id, request.host_id, request)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_create",
            resource_type="tunnel",
            resource_id=tunnel.id,
            details={"name": tunnel.name, "type": tunnel.tunnel_type}
        )

        return tunnel
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_create_error",
            resource_type="tunnel",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[TunnelResponse])
async def list_tunnels(
    host_id: str = Query(None, description="Filter by host ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List tunnels for current user.

    Args:
        host_id: Optional filter by host ID
        db: Database session
        user: Authenticated user

    Returns:
        List of TunnelResponse

    Raises:
        404: Host not found (when filtering)
    """
    try:
        # Verify host exists if filtering (and user owns it)
        if host_id:
            host = await host_service.get_host(db, host_id)
            if not host:
                raise HTTPException(status_code=404, detail="Host not found")

            if host.user_id != user.id:
                raise HTTPException(status_code=403, detail="Access denied")

        # List tunnels
        tunnels = await tunnel_service.list_tunnels(db, user.id, host_id)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_list",
            resource_type="tunnel",
            details={"host_id": host_id, "count": len(tunnels)}
        )

        return tunnels
    except HTTPException:
        raise
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_list_error",
            resource_type="tunnel",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tunnel_id}/status", response_model=TunnelStatusInfo)
async def get_tunnel_status(
    tunnel_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get tunnel status information.

    Args:
        tunnel_id: Tunnel ID
        db: Database session
        user: Authenticated user

    Returns:
        TunnelStatusInfo

    Raises:
        404: Tunnel not found
    """
    try:
        status = await tunnel_service.get_tunnel_status(db, user.id, tunnel_id)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_status",
            resource_type="tunnel",
            resource_id=tunnel_id,
            details={"status": status.status}
        )

        return status
    except ValueError:
        raise HTTPException(status_code=404, detail="Tunnel not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tunnel_id}", response_model=TunnelResponse)
async def update_tunnel(
    tunnel_id: str,
    request: TunnelUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update tunnel configuration.

    Args:
        tunnel_id: Tunnel ID
        request: Update request
        db: Database session
        user: Authenticated user

    Returns:
        Updated TunnelResponse

    Raises:
        404: Tunnel not found
        403: User does not have access
    """
    try:
        tunnel = await tunnel_service.update_tunnel(db, user.id, tunnel_id, request)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_update",
            resource_type="tunnel",
            resource_id=tunnel_id,
            details={"updated_fields": request.model_dump(exclude_unset=True)}
        )

        return tunnel
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_update_error",
            resource_type="tunnel",
            resource_id=tunnel_id,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tunnel_id}")
async def delete_tunnel(
    tunnel_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete tunnel.

    Args:
        tunnel_id: Tunnel ID
        db: Database session
        user: Authenticated user

    Returns:
        Success message

    Raises:
        404: Tunnel not found
        403: User does not have access
    """
    try:
        # Stop tunnel first if running
        await tunnel_manager.stop_tunnel_connection(user.id, tunnel_id)

        # Delete tunnel
        deleted = await tunnel_service.delete_tunnel(db, user.id, tunnel_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Tunnel not found")

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_delete",
            resource_type="tunnel",
            resource_id=tunnel_id,
        )

        return {"message": "Tunnel deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_delete_error",
            resource_type="tunnel",
            resource_id=tunnel_id,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{tunnel_id}/start")
async def start_tunnel(
    tunnel_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start tunnel connection.

    Args:
        tunnel_id: Tunnel ID
        db: Database session
        user: Authenticated user

    Returns:
        Success message

    Raises:
        404: Tunnel not found
    """
    try:
        tunnel = await tunnel_service.get_tunnel(db, user.id, tunnel_id)
        if not tunnel:
            raise HTTPException(status_code=404, detail="Tunnel not found")

        # Get host and credentials
        host = await host_service.get_host(db, tunnel.host_id)
        credential = await credential_service.get_primary_credential(db, tunnel.host_id)

        if not host or not credential:
            raise HTTPException(status_code=400, detail="Host or credentials not available")

        # Start tunnel
        success = await tunnel_manager.start_tunnel_connection(
            db, user.id, tunnel_id, host, credential
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to start tunnel")

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_start",
            resource_type="tunnel",
            resource_id=tunnel_id,
        )

        return {"message": "Tunnel started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="tunnel_start_error",
            resource_type="tunnel",
            resource_id=tunnel_id,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{tunnel_id}/stop")
async def stop_tunnel(
    tunnel_id: str,
    user: User = Depends(get_current_user),
):
    """Stop tunnel connection.

    Args:
        tunnel_id: Tunnel ID
        user: Authenticated user

    Returns:
        Success message

    Raises:
        404: Tunnel not found
    """
    try:
        success = await tunnel_manager.stop_tunnel_connection(user.id, tunnel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tunnel not found")

        return {"message": "Tunnel stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

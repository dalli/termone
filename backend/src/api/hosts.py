"""Hosts API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.hosts import (
    HostCreate,
    HostUpdate,
    HostResponse,
    HostListResponse,
    PublicKeyDeployRequest,
    PublicKeyDeployResponse,
    HostSearchRequest,
)
from src.services.host_service import HostService
from src.services.credential_service import CredentialService
from src.services.audit_service import AuditService
from src.services.encryption import EncryptionService
from src.services.permission_service import PermissionService
from src.middleware.auth import verify_token
from src.exceptions import (
    NotFoundException,
    PermissionException,
    ValidationException,
)

router = APIRouter(prefix="/hosts", tags=["hosts"])


def get_host_service(encryption_service: EncryptionService = Depends()) -> HostService:
    """Get host service with dependencies."""
    credential_service = CredentialService(encryption_service)
    return HostService(credential_service)


def get_credential_service(
    encryption_service: EncryptionService = Depends(),
) -> CredentialService:
    """Get credential service with dependencies."""
    return CredentialService(encryption_service)


def get_audit_service() -> AuditService:
    """Get audit service."""
    return AuditService()


def get_permission_service() -> PermissionService:
    """Get permission service."""
    return PermissionService()


@router.post(
    "",
    response_model=HostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new SSH host",
    description="Register a new SSH host with credentials",
)
async def create_host(
    request: Request,
    host_data: HostCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Create a new SSH host."""
    try:
        # Create the host with credential
        host = await host_service.create_host(
            db,
            hostname=host_data.hostname,
            port=host_data.port,
            username=host_data.username,
            user_id=current_user["user_id"],
            tags=host_data.tags,
            folder=host_data.folder,
            description=host_data.description,
            credential_type=host_data.credential.type.value,
            credential_value=host_data.credential.value,
        )

        # Log the action
        await audit_service.log_host_created(
            db,
            current_user["user_id"],
            host.id,
            host.hostname,
            ip_address=request.client.host if request.client else None,
        )

        return HostResponse.model_validate(host)

    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    response_model=HostListResponse,
    summary="List SSH hosts",
    description="Get a paginated list of SSH hosts for the current user",
)
async def list_hosts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter"),
    folder: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
):
    """List hosts for the current user."""
    try:
        # Parse tags from comma-separated string
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        hosts, total = await host_service.list_hosts(
            db,
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit,
            tags=tag_list,
            folder=folder,
            is_active=is_active,
        )

        return HostListResponse(
            items=[HostResponse.model_validate(host) for host in hosts],
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search",
    response_model=HostListResponse,
    summary="Search SSH hosts",
    description="Full-text search for SSH hosts",
)
async def search_hosts(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Search hosts by hostname or description."""
    try:
        hosts, total = await host_service.search_hosts(
            db,
            user_id=current_user["user_id"],
            query=q,
            skip=skip,
            limit=limit,
        )

        # Log the search
        await audit_service.log_search(
            db,
            current_user["user_id"],
            q,
            total,
        )

        return HostListResponse(
            items=[HostResponse.model_validate(host) for host in hosts],
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{host_id}",
    response_model=HostResponse,
    summary="Get a specific SSH host",
    description="Retrieve details of a specific SSH host",
)
async def get_host(
    host_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    permission_service: PermissionService = Depends(get_permission_service),
):
    """Get a specific host."""
    try:
        # Verify permission
        await permission_service.check_host_access(
            db,
            current_user["user_id"],
            host_id,
            "read",
        )

        host = await host_service.get_host(db, host_id, current_user["user_id"])
        return HostResponse.model_validate(host)

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{host_id}",
    response_model=HostResponse,
    summary="Update a SSH host",
    description="Update host configuration",
)
async def update_host(
    host_id: str,
    host_data: HostUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    credential_service: CredentialService = Depends(get_credential_service),
    audit_service: AuditService = Depends(get_audit_service),
    permission_service: PermissionService = Depends(get_permission_service),
):
    """Update a host."""
    try:
        # Verify permission
        await permission_service.check_host_access(
            db,
            current_user["user_id"],
            host_id,
            "write",
        )

        # Get original host for audit logging
        original_host = await host_service.get_host(db, host_id, current_user["user_id"])

        # Prepare update data
        update_dict = {}
        if host_data.hostname:
            update_dict["hostname"] = host_data.hostname
        if host_data.port:
            update_dict["port"] = host_data.port
        if host_data.username:
            update_dict["username"] = host_data.username
        if host_data.tags is not None:
            update_dict["tags"] = host_data.tags
        if host_data.folder is not None:
            update_dict["folder"] = host_data.folder
        if host_data.description is not None:
            update_dict["description"] = host_data.description
        if host_data.is_active is not None:
            update_dict["is_active"] = host_data.is_active

        # Update host
        updated_host = await host_service.update_host(
            db,
            host_id,
            current_user["user_id"],
            **update_dict,
        )

        # Update credential if provided
        if host_data.credential:
            existing_credential = await credential_service.get_host_credential(
                db, host_id
            )
            if existing_credential:
                await credential_service.update_credential(
                    db,
                    existing_credential.id,
                    host_data.credential.value,
                    host_data.credential.type.value,
                )
            else:
                await credential_service.create_credential(
                    db,
                    host_id,
                    host_data.credential.type.value,
                    host_data.credential.value,
                )

        # Log the update
        await audit_service.log_host_updated(
            db,
            current_user["user_id"],
            host_id,
            update_dict,
            ip_address=request.client.host if request.client else None,
        )

        return HostResponse.model_validate(updated_host)

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{host_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a SSH host",
    description="Delete a host and all associated data",
)
async def delete_host(
    host_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    audit_service: AuditService = Depends(get_audit_service),
    permission_service: PermissionService = Depends(get_permission_service),
):
    """Delete a host."""
    try:
        # Verify permission
        await permission_service.check_host_access(
            db,
            current_user["user_id"],
            host_id,
            "delete",
        )

        # Get host details for audit
        host = await host_service.get_host(db, host_id, current_user["user_id"])

        # Delete the host
        await host_service.delete_host(db, host_id, current_user["user_id"])

        # Log the deletion
        await audit_service.log_host_deleted(
            db,
            current_user["user_id"],
            host_id,
            host.hostname,
            ip_address=request.client.host if request.client else None,
        )

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{host_id}/deploy-public-key",
    response_model=PublicKeyDeployResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Deploy public key to host",
    description="Deploy a public key for passwordless SSH access",
)
async def deploy_public_key(
    host_id: str,
    key_data: PublicKeyDeployRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    audit_service: AuditService = Depends(get_audit_service),
    permission_service: PermissionService = Depends(get_permission_service),
):
    """Deploy a public key to a host."""
    try:
        # Verify permission
        await permission_service.check_host_access(
            db,
            current_user["user_id"],
            host_id,
            "write",
        )

        # Get the host
        host = await host_service.get_host(db, host_id, current_user["user_id"])

        # In a real implementation, this would trigger an async task to deploy the key
        # For now, we'll just return a response indicating the deployment was accepted

        # Log the deployment request
        await audit_service.log_public_key_deployment(
            db,
            current_user["user_id"],
            host_id,
            "pending",
            ip_address=request.client.host if request.client else None,
        )

        return PublicKeyDeployResponse(
            host_id=host.id,
            status="pending",
            message="Public key deployment initiated",
            deployment_id=f"deploy-{host.id}-{current_user['user_id']}",
        )

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{host_id}/tags/{tag}",
    response_model=HostResponse,
    summary="Add tag to host",
    description="Add a tag to organize the host",
)
async def add_tag_to_host(
    host_id: str,
    tag: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    permission_service: PermissionService = Depends(get_permission_service),
):
    """Add a tag to a host."""
    try:
        # Verify permission
        await permission_service.check_host_access(
            db,
            current_user["user_id"],
            host_id,
            "write",
        )

        host = await host_service.add_tag_to_host(
            db, host_id, tag, current_user["user_id"]
        )
        return HostResponse.model_validate(host)

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{host_id}/tags/{tag}",
    response_model=HostResponse,
    summary="Remove tag from host",
    description="Remove a tag from a host",
)
async def remove_tag_from_host(
    host_id: str,
    tag: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    host_service: HostService = Depends(get_host_service),
    permission_service: PermissionService = Depends(get_permission_service),
):
    """Remove a tag from a host."""
    try:
        # Verify permission
        await permission_service.check_host_access(
            db,
            current_user["user_id"],
            host_id,
            "write",
        )

        host = await host_service.remove_tag_from_host(
            db, host_id, tag, current_user["user_id"]
        )
        return HostResponse.model_validate(host)

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

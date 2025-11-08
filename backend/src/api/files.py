"""File management API endpoints.

Provides SFTP-based file operations:
- GET /files/{host_id}/list: Directory listing
- GET /files/{host_id}/download: File download
- POST /files/{host_id}/upload: File upload
- POST /files/{host_id}/edit: File read/write
- POST /files/{host_id}/delete: File delete
- POST /files/{host_id}/chmod: Permission change
- POST /files/{host_id}/move: File move/rename
"""

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.models import SSHHost, User
from src.schemas.files import (
    ChmodRequest,
    ChmodResponse,
    DeleteRequest,
    DeleteResponse,
    DirectoryListing,
    EditRequest,
    EditResponse,
    FileOperationError,
    MkdirRequest,
    MkdirResponse,
    MoveRequest,
    MoveResponse,
    UploadResponse,
)
from src.services.audit_service import AuditService
from src.services.credential_service import CredentialService
from src.services.file_service import FileService
from src.services.host_service import HostService


router = APIRouter(prefix="/files", tags=["files"])


# Service instances
credential_service = CredentialService()
file_service = FileService(credential_service)
host_service = HostService()
audit_service = AuditService()


@router.get("/{host_id}/list", response_model=DirectoryListing)
async def list_directory(
    host_id: str,
    path: str = Query(".", description="Directory path to list"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List directory contents.

    Args:
        host_id: SSH host ID
        path: Directory path (default: .)
        db: Database session
        user: Authenticated user

    Returns:
        Directory listing with file metadata

    Raises:
        404: Host not found
        403: User does not have access to host
        400: Directory operation failed
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential for host
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # List directory
        entries = await file_service.list_directory(db, host, credential, path)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_list",
            resource_type="file",
            resource_id=host_id,
            details={"path": path}
        )

        return DirectoryListing(entries=entries, path=path)
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_list_error",
            resource_type="file",
            resource_id=host_id,
            details={"path": path, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{host_id}/download")
async def download_file(
    host_id: str,
    path: str = Query(..., description="Remote file path"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download file from remote host.

    Args:
        host_id: SSH host ID
        path: Remote file path
        db: Database session
        user: Authenticated user

    Returns:
        File content as binary stream

    Raises:
        404: Host or file not found
        403: User does not have access
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # Download file
        file_content = await file_service.download_file(db, host, credential, path)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_download",
            resource_type="file",
            resource_id=host_id,
            details={"path": path, "size": len(file_content)}
        )

        # Return as streaming response
        return StreamingResponse(
            iter([file_content]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"}
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_download_error",
            resource_type="file",
            resource_id=host_id,
            details={"path": path, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{host_id}/upload", response_model=UploadResponse)
async def upload_file(
    host_id: str,
    path: str = Query(..., description="Destination directory path"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload file to remote host.

    Args:
        host_id: SSH host ID
        path: Destination directory path
        file: File to upload
        db: Database session
        user: Authenticated user

    Returns:
        Upload response with file path and size

    Raises:
        404: Host not found
        403: User does not have access
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # Create temporary file for upload
        import tempfile
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Construct remote path
            remote_path = f"{path.rstrip('/')}/{file.filename}"

            # Upload file
            result = await file_service.upload_file(db, host, credential, tmp_path, remote_path)

            # Audit log
            await audit_service.log_action(
                db,
                user_id=user.id,
                action="file_upload",
                resource_type="file",
                resource_id=host_id,
                details={"path": remote_path, "size": result["size"]}
            )

            return UploadResponse(**result)
        finally:
            # Clean up temporary file
            import os
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied for upload")
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_upload_error",
            resource_type="file",
            resource_id=host_id,
            details={"filename": file.filename, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{host_id}/edit", response_model=EditResponse)
async def edit_file(
    host_id: str,
    request: EditRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Read or write file content.

    Args:
        host_id: SSH host ID
        request: Edit request with path and content
        db: Database session
        user: Authenticated user

    Returns:
        Edit response with file path and size

    Raises:
        404: Host or file not found
        403: User does not have access
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # Write file
        result = await file_service.write_file(
            db,
            host,
            credential,
            request.path,
            request.content,
            encoding=request.encoding or "utf-8"
        )

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_edit",
            resource_type="file",
            resource_id=host_id,
            details={"path": request.path, "size": result["size"]}
        )

        return EditResponse(**result)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied for edit")
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_edit_error",
            resource_type="file",
            resource_id=host_id,
            details={"path": request.path, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{host_id}/chmod", response_model=ChmodResponse)
async def chmod_file(
    host_id: str,
    request: ChmodRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Change file permissions.

    Args:
        host_id: SSH host ID
        request: Chmod request with path and mode
        db: Database session
        user: Authenticated user

    Returns:
        Chmod response with file path and mode

    Raises:
        404: Host or file not found
        403: User does not have access
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # Change permissions
        result = await file_service.chmod_file(
            db,
            host,
            credential,
            request.path,
            request.mode
        )

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_chmod",
            resource_type="file",
            resource_id=host_id,
            details={"path": request.path, "mode": request.mode}
        )

        return ChmodResponse(**result)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_chmod_error",
            resource_type="file",
            resource_id=host_id,
            details={"path": request.path, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{host_id}/delete", response_model=DeleteResponse)
async def delete_file(
    host_id: str,
    request: DeleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete file.

    Args:
        host_id: SSH host ID
        request: Delete request with path
        db: Database session
        user: Authenticated user

    Returns:
        Delete response

    Raises:
        404: Host or file not found
        403: User does not have access
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # Delete file
        result = await file_service.delete_file(db, host, credential, request.path)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_delete",
            resource_type="file",
            resource_id=host_id,
            details={"path": request.path}
        )

        return DeleteResponse(**result)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_delete_error",
            resource_type="file",
            resource_id=host_id,
            details={"path": request.path, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{host_id}/move", response_model=MoveResponse)
async def move_file(
    host_id: str,
    request: MoveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Move or rename file.

    Args:
        host_id: SSH host ID
        request: Move request with old and new paths
        db: Database session
        user: Authenticated user

    Returns:
        Move response

    Raises:
        404: Host or file not found
        403: User does not have access
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # Rename file
        result = await file_service.rename_file(
            db,
            host,
            credential,
            request.old_path,
            request.new_path
        )

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_move",
            resource_type="file",
            resource_id=host_id,
            details={"old_path": request.old_path, "new_path": request.new_path}
        )

        return MoveResponse(**result)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="file_move_error",
            resource_type="file",
            resource_id=host_id,
            details={"old_path": request.old_path, "new_path": request.new_path, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{host_id}/mkdir", response_model=MkdirResponse)
async def create_directory(
    host_id: str,
    request: MkdirRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create directory.

    Args:
        host_id: SSH host ID
        request: Mkdir request with path
        db: Database session
        user: Authenticated user

    Returns:
        Mkdir response

    Raises:
        404: Host not found
        403: User does not have access
    """
    # Get host and verify access
    host = await host_service.get_host(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    if host.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Get primary credential
        credential = await credential_service.get_primary_credential(db, host_id)
        if not credential:
            raise HTTPException(status_code=400, detail="No credentials available for host")

        # Create directory
        result = await file_service.create_directory(
            db,
            host,
            credential,
            request.path,
            mode=request.mode or 0o755
        )

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="dir_create",
            resource_type="directory",
            resource_id=host_id,
            details={"path": request.path}
        )

        return MkdirResponse(**result)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except FileExistsError:
        raise HTTPException(status_code=400, detail="Directory already exists")
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="dir_create_error",
            resource_type="directory",
            resource_id=host_id,
            details={"path": request.path, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))

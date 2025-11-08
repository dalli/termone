"""Snippet management API endpoints.

Provides SSH command snippet management:
- POST /snippets: Create snippet
- GET /snippets: List snippets
- GET /snippets/{snippet_id}: Get snippet
- PUT /snippets/{snippet_id}: Update snippet
- DELETE /snippets/{snippet_id}: Delete snippet
- POST /snippets/{snippet_id}/execute: Execute snippet
- POST /snippets/{snippet_id}/broadcast: Broadcast to sessions
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.models import User
from src.schemas.snippets import (
    SnippetCreate,
    SnippetUpdate,
    SnippetResponse,
    SnippetExecuteRequest,
    SnippetBroadcastRequest,
    SnippetExecutionResult,
)
from src.services.snippet_service import SnippetService
from src.services.audit_service import AuditService

router = APIRouter(prefix="/snippets", tags=["snippets"])

# Service instances
snippet_service = SnippetService()
audit_service = AuditService()


@router.post("", response_model=SnippetResponse)
async def create_snippet(
    request: SnippetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create new command snippet.

    Args:
        request: Snippet creation request
        db: Database session
        user: Authenticated user

    Returns:
        SnippetResponse with snippet details
    """
    try:
        snippet = await snippet_service.create_snippet(user.id, request)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_create",
            resource_type="snippet",
            resource_id=snippet.id,
            details={"name": snippet.name, "tags": snippet.tags}
        )

        return snippet
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_create_error",
            resource_type="snippet",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[SnippetResponse])
async def list_snippets(
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List snippets for current user.

    Args:
        tags: Optional tag filter
        db: Database session
        user: Authenticated user

    Returns:
        List of SnippetResponse
    """
    try:
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        snippets = await snippet_service.list_snippets(user.id, tags=tag_list)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_list",
            resource_type="snippet",
            details={"tags": tag_list, "count": len(snippets)}
        )

        return snippets
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{snippet_id}", response_model=SnippetResponse)
async def get_snippet(
    snippet_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get snippet by ID.

    Args:
        snippet_id: Snippet ID
        db: Database session
        user: Authenticated user

    Returns:
        SnippetResponse

    Raises:
        404: Snippet not found
    """
    snippet = await snippet_service.get_snippet(user.id, snippet_id)
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    return snippet


@router.put("/{snippet_id}", response_model=SnippetResponse)
async def update_snippet(
    snippet_id: str,
    request: SnippetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update snippet.

    Args:
        snippet_id: Snippet ID
        request: Update request
        db: Database session
        user: Authenticated user

    Returns:
        Updated SnippetResponse

    Raises:
        404: Snippet not found
        403: Access denied
    """
    try:
        snippet = await snippet_service.update_snippet(user.id, snippet_id, request)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_update",
            resource_type="snippet",
            resource_id=snippet_id,
            details={"updated_fields": request.model_dump(exclude_unset=True)}
        )

        return snippet
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{snippet_id}")
async def delete_snippet(
    snippet_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete snippet.

    Args:
        snippet_id: Snippet ID
        db: Database session
        user: Authenticated user

    Returns:
        Success message

    Raises:
        404: Snippet not found
    """
    try:
        deleted = await snippet_service.delete_snippet(user.id, snippet_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Snippet not found")

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_delete",
            resource_type="snippet",
            resource_id=snippet_id,
        )

        return {"message": "Snippet deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{snippet_id}/execute", response_model=SnippetExecutionResult)
async def execute_snippet(
    snippet_id: str,
    request: SnippetExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Execute snippet in terminal session.

    Args:
        snippet_id: Snippet ID
        request: Execution request
        db: Database session
        user: Authenticated user

    Returns:
        Execution result with ID

    Raises:
        404: Snippet not found
        403: Access denied
    """
    try:
        execution = await snippet_service.execute_snippet(user.id, snippet_id, request)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_execute",
            resource_type="snippet",
            resource_id=snippet_id,
            details={
                "session_id": request.session_id,
                "host_id": request.target_host_id,
            }
        )

        return SnippetExecutionResult(
            execution_id=execution["execution_id"],
            snippet_id=snippet_id,
            session_id=request.session_id,
            status="pending",
            started_at=execution["started_at"],
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_execute_error",
            resource_type="snippet",
            resource_id=snippet_id,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{snippet_id}/broadcast")
async def broadcast_snippet(
    snippet_id: str,
    request: SnippetBroadcastRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Broadcast snippet to multiple terminal sessions.

    Args:
        snippet_id: Snippet ID
        request: Broadcast request
        db: Database session
        user: Authenticated user

    Returns:
        Broadcast result

    Raises:
        404: Snippet not found
        403: Access denied
    """
    try:
        broadcast = await snippet_service.broadcast_snippet(user.id, snippet_id, request)

        # Audit log
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_broadcast",
            resource_type="snippet",
            resource_id=snippet_id,
            details={
                "session_count": len(request.session_ids),
                "host_id": request.target_host_id,
            }
        )

        return {
            "broadcast_id": broadcast["broadcast_id"],
            "snippet_id": snippet_id,
            "sessions": request.session_ids,
            "status": "pending",
        }
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        await audit_service.log_action(
            db,
            user_id=user.id,
            action="snippet_broadcast_error",
            resource_type="snippet",
            resource_id=snippet_id,
            details={"error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))

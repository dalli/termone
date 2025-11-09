"""Terminal API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.terminal import (
    TerminalSessionCreate,
    TerminalSessionResponse,
    TerminalSessionListResponse,
    TerminalResizeRequest,
    TerminalInputRequest,
)
from src.services.terminal_service import TerminalSessionService
from src.services.credential_service import CredentialService
from src.services.encryption import EncryptionService
from src.services.audit_service import AuditService
from src.middleware.auth import verify_token
from src.exceptions import NotFoundException, PermissionException, ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/terminal", tags=["terminal"])


def get_terminal_service(
    encryption_service: EncryptionService = Depends(),
) -> TerminalSessionService:
    """Get terminal service with dependencies."""
    credential_service = CredentialService(encryption_service)
    return TerminalSessionService(credential_service)


def get_audit_service() -> AuditService:
    """Get audit service."""
    return AuditService()


@router.post(
    "/sessions/{host_id}",
    response_model=TerminalSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create terminal session",
    description="Create a new terminal session for an SSH host",
)
async def create_terminal_session(
    host_id: str,
    request: Request,
    session_data: TerminalSessionCreate = TerminalSessionCreate(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    terminal_service: TerminalSessionService = Depends(get_terminal_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Create a new terminal session."""
    try:
        terminal_session = await terminal_service.create_session(
            db,
            host_id=host_id,
            user_id=current_user["user_id"],
            rows=session_data.rows,
            cols=session_data.cols,
            env=session_data.env,
        )

        # Log the action
        await audit_service.log_action(
            db,
            current_user["user_id"],
            action="create",
            resource_type="terminal_session",
            resource_id=terminal_session.id,
            details={"host_id": host_id, "rows": session_data.rows, "cols": session_data.cols},
            ip_address=request.client.host if request.client else None,
        )

        return TerminalSessionResponse.model_validate(terminal_session)

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create terminal session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sessions",
    response_model=TerminalSessionListResponse,
    summary="List terminal sessions",
    description="Get list of active terminal sessions",
)
async def list_terminal_sessions(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    terminal_service: TerminalSessionService = Depends(get_terminal_service),
):
    """List all terminal sessions for the current user."""
    try:
        sessions = await terminal_service.list_sessions(
            db,
            user_id=current_user["user_id"],
        )

        return TerminalSessionListResponse(
            items=[TerminalSessionResponse.model_validate(s) for s in sessions],
            total=len(sessions),
        )

    except Exception as e:
        logger.error(f"Failed to list terminal sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete terminal session",
    description="Close and delete a terminal session",
)
async def delete_terminal_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    terminal_service: TerminalSessionService = Depends(get_terminal_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Close a terminal session."""
    try:
        await terminal_service.close_session(
            db,
            session_id=session_id,
            user_id=current_user["user_id"],
        )

        # Log the action
        await audit_service.log_action(
            db,
            current_user["user_id"],
            action="delete",
            resource_type="terminal_session",
            resource_id=session_id,
            ip_address=request.client.host if request.client else None,
        )

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Failed to close terminal session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def websocket_terminal(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    terminal_service: TerminalSessionService = Depends(get_terminal_service),
):
    """WebSocket endpoint for terminal I/O streaming."""
    try:
        await websocket.accept()

        # Get session data
        session_data = terminal_service.get_session_data(session_id)
        if not session_data:
            await websocket.close(code=4004, reason="Session not found")
            return

        # Spawn PTY if not already spawned
        if not session_data.get("process"):
            try:
                await terminal_service.spawn_pty(session_id)
            except Exception as e:
                logger.error(f"Failed to spawn PTY: {e}")
                await websocket.close(code=4000, reason="Failed to spawn PTY")
                return

        process = session_data["process"]
        ssh_client = session_data["ssh_client"]

        # Handle incoming messages
        try:
            while True:
                # Receive message from client
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                except asyncio.TimeoutError:
                    # Send ping
                    try:
                        await websocket.send_json({"type": "ping"})
                    except:
                        break
                    continue

                # Parse message
                import json
                try:
                    msg = json.loads(message)
                except:
                    continue

                msg_type = msg.get("type")
                data = msg.get("data", "")

                # Handle different message types
                if msg_type == "input":
                    # Send input to PTY
                    try:
                        process.stdin.write(data.encode() if isinstance(data, str) else data)
                        await process.stdin.drain()
                    except Exception as e:
                        logger.error(f"Error writing to PTY: {e}")
                        break

                elif msg_type == "resize":
                    # Resize terminal
                    cols = msg.get("cols", 80)
                    rows = msg.get("rows", 24)
                    await terminal_service.resize_terminal(session_id, rows, cols)

                elif msg_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})

                # Update activity
                await terminal_service.update_activity(session_id)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")

        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")


import asyncio


async def read_pty_output(session_id: str, websocket: WebSocket, process, terminal_service):
    """Read PTY output and send to WebSocket."""
    try:
        while True:
            try:
                # Read from PTY with timeout
                data = await asyncio.wait_for(
                    process.stdout.readexactly(1024),
                    timeout=1,
                )

                if not data:
                    break

                # Send to WebSocket
                try:
                    await websocket.send_json({
                        "type": "output",
                        "data": data.decode(errors="replace"),
                    })
                except:
                    break

                # Update activity
                await terminal_service.update_activity(session_id)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Error reading PTY output: {e}")
                break

    except Exception as e:
        logger.error(f"Error in read_pty_output: {e}")


@router.post(
    "/sessions/{session_id}/resize",
    summary="Resize terminal",
    description="Resize a terminal session",
)
async def resize_terminal(
    session_id: str,
    resize_data: TerminalResizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    terminal_service: TerminalSessionService = Depends(get_terminal_service),
):
    """Resize a terminal."""
    try:
        # Verify session ownership
        await terminal_service.get_session(db, session_id, current_user["user_id"])

        success = await terminal_service.resize_terminal(
            session_id,
            rows=resize_data.rows,
            cols=resize_data.cols,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to resize terminal")

        return {"success": True, "rows": resize_data.rows, "cols": resize_data.cols}

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Failed to resize terminal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

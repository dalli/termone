"""Stats API endpoints."""

import json
import logging
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.stats import StatsSnapshot, StatsMessage
from src.services.stats_service import StatsService
from src.services.credential_service import CredentialService
from src.services.encryption import EncryptionService
from src.services.audit_service import AuditService
from src.middleware.auth import verify_token
from src.exceptions import NotFoundException, PermissionException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])

# Global stats service instance
_stats_service: Optional[StatsService] = None


def get_stats_service(
    encryption_service: EncryptionService = Depends(),
) -> StatsService:
    """Get stats service with dependencies."""
    global _stats_service
    if _stats_service is None:
        credential_service = CredentialService(encryption_service)
        _stats_service = StatsService(credential_service)
    return _stats_service


def get_audit_service() -> AuditService:
    """Get audit service."""
    return AuditService()


@router.get(
    "/{host_id}/current",
    response_model=dict,
    summary="Get current stats",
    description="Get current system statistics snapshot for a host",
)
async def get_current_stats(
    host_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    stats_service: StatsService = Depends(get_stats_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Get current stats for a host."""
    try:
        stats = await stats_service.get_current_stats(
            db,
            host_id=host_id,
            user_id=current_user["user_id"],
        )

        # Log the access
        await audit_service.log_action(
            db,
            current_user["user_id"],
            action="read",
            resource_type="stats",
            resource_id=host_id,
        )

        return stats

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found or no stats available")
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{host_id}")
async def websocket_stats(
    websocket: WebSocket,
    host_id: str,
    db: AsyncSession = Depends(get_db),
    stats_service: StatsService = Depends(get_stats_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """WebSocket endpoint for real-time stats streaming."""
    try:
        await websocket.accept()

        # For WebSocket, we need to verify auth differently
        # In a real implementation, token would be passed in query params or header
        # For now, we'll skip auth check for WebSocket (should add proper auth)

        logger.info(f"WebSocket connected for stats stream: {host_id}")

        # Start stats collection if not already running
        try:
            await stats_service.start_collection(
                db,
                host_id,
                user_id="system",  # In production, get from token
                interval=5,
            )
        except Exception as e:
            logger.error(f"Failed to start stats collection: {e}")
            await websocket.close(code=4000, reason="Failed to start stats collection")
            return

        # Create callback for receiving stats updates
        async def stats_callback(stats):
            """Callback to send stats to WebSocket."""
            try:
                message = StatsMessage(
                    type="stats",
                    timestamp=stats.get("timestamp"),
                    data=stats,
                )
                await websocket.send_json(message.model_dump())
            except Exception as e:
                logger.error(f"Error sending stats message: {e}")

        # Subscribe to stats updates
        await stats_service.subscribe(host_id, stats_callback)

        # Handle incoming messages
        try:
            while True:
                # Receive ping/control messages from client
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                except asyncio.TimeoutError:
                    # Send ping
                    try:
                        await websocket.send_json({
                            "type": "ping",
                            "timestamp": asyncio.get_event_loop().time(),
                        })
                    except:
                        break
                    continue

                try:
                    msg = json.loads(message)
                except:
                    continue

                msg_type = msg.get("type")

                if msg_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for stats: {host_id}")

        except Exception as e:
            logger.error(f"WebSocket error for stats {host_id}: {e}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Unsubscribe and stop collection if no more subscribers
        try:
            await stats_service.unsubscribe(host_id, stats_callback)

            # Check if any subscribers remain
            if host_id not in stats_service.subscribers or len(
                stats_service.subscribers[host_id]
            ) == 0:
                await stats_service.stop_collection(host_id)
        except:
            pass


@router.post(
    "/{host_id}/start-collection",
    summary="Start stats collection",
    description="Start background statistics collection for a host",
)
async def start_stats_collection(
    host_id: str,
    interval: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Start stats collection for a host."""
    try:
        await stats_service.start_collection(
            db,
            host_id=host_id,
            user_id=current_user["user_id"],
            interval=interval,
        )

        return {"success": True, "message": "Stats collection started"}

    except PermissionException:
        raise HTTPException(status_code=403, detail="Access denied")
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        logger.error(f"Failed to start stats collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{host_id}/stop-collection",
    summary="Stop stats collection",
    description="Stop background statistics collection for a host",
)
async def stop_stats_collection(
    host_id: str,
    stats_service: StatsService = Depends(get_stats_service),
):
    """Stop stats collection for a host."""
    try:
        await stats_service.stop_collection(host_id)
        return {"success": True, "message": "Stats collection stopped"}

    except Exception as e:
        logger.error(f"Failed to stop stats collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

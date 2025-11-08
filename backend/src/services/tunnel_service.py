"""Tunnel service for SSH port forwarding management.

Provides high-level tunnel operations:
- Create, read, update, delete tunnels
- Start/stop tunnel connections
- Monitor tunnel status
- Automatic reconnection on failure
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import SSHHost, Credential, User
from src.schemas.tunnels import (
    TunnelCreate,
    TunnelUpdate,
    TunnelResponse,
    TunnelStatus,
    TunnelStatusInfo,
)
from src.services.credential_service import CredentialService
from src.services.ssh_client import SSHClient


class TunnelInfo:
    """In-memory tunnel information storage."""

    def __init__(self, tunnel_id: str, create_data: TunnelCreate):
        self.id = tunnel_id
        self.host_id = create_data.host_id
        self.name = create_data.name
        self.tunnel_type = create_data.tunnel_type
        self.local_port = create_data.local_port
        self.remote_host = create_data.remote_host
        self.remote_port = create_data.remote_port
        self.bind_address = create_data.bind_address or "127.0.0.1"
        self.enabled = create_data.enabled != False
        self.auto_reconnect = create_data.auto_reconnect != False
        self.status = TunnelStatus.DISCONNECTED
        self.connected = False
        self.error: Optional[str] = None
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.last_connection_time: Optional[str] = None
        self.last_disconnection_time: Optional[str] = None
        self.connection_start_time: Optional[float] = None
        self.ssh_client: Optional[SSHClient] = None
        self.forward_task: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "host_id": self.host_id,
            "name": self.name,
            "tunnel_type": self.tunnel_type.value,
            "local_port": self.local_port,
            "remote_host": self.remote_host,
            "remote_port": self.remote_port,
            "bind_address": self.bind_address,
            "status": self.status.value,
            "connected": self.connected,
            "enabled": self.enabled,
            "auto_reconnect": self.auto_reconnect,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }

    @property
    def uptime_seconds(self) -> int:
        """Get current connection uptime in seconds."""
        if not self.connection_start_time:
            return 0
        return int(asyncio.get_event_loop().time() - self.connection_start_time)


class TunnelService:
    """High-level tunnel management service."""

    def __init__(self, credential_service: CredentialService):
        """Initialize tunnel service.

        Args:
            credential_service: Credential service for SSH connections
        """
        self.credential_service = credential_service
        self.tunnels: Dict[str, TunnelInfo] = {}
        self.user_tunnels: Dict[str, List[str]] = {}  # user_id -> [tunnel_ids]

    async def create_tunnel(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: str,
        create_data: TunnelCreate,
    ) -> TunnelResponse:
        """Create new tunnel.

        Args:
            db: Database session
            user_id: User ID
            host_id: SSH host ID
            create_data: Tunnel creation data

        Returns:
            TunnelResponse with tunnel details
        """
        # Verify host exists and user owns it
        from src.services.host_service import HostService
        host_service = HostService()
        host = await host_service.get_host(db, host_id)
        if not host or host.user_id != user_id:
            raise ValueError("Host not found or access denied")

        # Create tunnel
        tunnel_id = str(uuid.uuid4())
        tunnel = TunnelInfo(tunnel_id, create_data)

        # Store tunnel
        self.tunnels[tunnel_id] = tunnel
        if user_id not in self.user_tunnels:
            self.user_tunnels[user_id] = []
        self.user_tunnels[user_id].append(tunnel_id)

        return TunnelResponse(**tunnel.to_dict())

    async def get_tunnel(
        self,
        db: AsyncSession,
        user_id: str,
        tunnel_id: str,
    ) -> Optional[TunnelResponse]:
        """Get tunnel by ID.

        Args:
            db: Database session
            user_id: User ID
            tunnel_id: Tunnel ID

        Returns:
            TunnelResponse or None if not found
        """
        tunnel = self.tunnels.get(tunnel_id)
        if not tunnel:
            return None

        # Verify user owns tunnel
        from src.services.host_service import HostService
        host_service = HostService()
        host = await host_service.get_host(db, tunnel.host_id)
        if not host or host.user_id != user_id:
            return None

        return TunnelResponse(**tunnel.to_dict())

    async def list_tunnels(
        self,
        db: AsyncSession,
        user_id: str,
        host_id: Optional[str] = None,
    ) -> List[TunnelResponse]:
        """List tunnels for user.

        Args:
            db: Database session
            user_id: User ID
            host_id: Optional filter by host ID

        Returns:
            List of TunnelResponse
        """
        tunnel_ids = self.user_tunnels.get(user_id, [])
        tunnels = []

        from src.services.host_service import HostService
        host_service = HostService()

        for tid in tunnel_ids:
            tunnel = self.tunnels.get(tid)
            if not tunnel:
                continue

            # Verify user still owns host
            host = await host_service.get_host(db, tunnel.host_id)
            if not host or host.user_id != user_id:
                continue

            if host_id and tunnel.host_id != host_id:
                continue

            tunnels.append(TunnelResponse(**tunnel.to_dict()))

        return tunnels

    async def update_tunnel(
        self,
        db: AsyncSession,
        user_id: str,
        tunnel_id: str,
        update_data: TunnelUpdate,
    ) -> TunnelResponse:
        """Update tunnel configuration.

        Args:
            db: Database session
            user_id: User ID
            tunnel_id: Tunnel ID
            update_data: Update data

        Returns:
            Updated TunnelResponse
        """
        tunnel = self.tunnels.get(tunnel_id)
        if not tunnel:
            raise ValueError("Tunnel not found")

        # Verify ownership
        from src.services.host_service import HostService
        host_service = HostService()
        host = await host_service.get_host(db, tunnel.host_id)
        if not host or host.user_id != user_id:
            raise ValueError("Access denied")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(tunnel, key, value)

        tunnel.updated_at = datetime.utcnow().isoformat()

        return TunnelResponse(**tunnel.to_dict())

    async def delete_tunnel(
        self,
        db: AsyncSession,
        user_id: str,
        tunnel_id: str,
    ) -> bool:
        """Delete tunnel.

        Args:
            db: Database session
            user_id: User ID
            tunnel_id: Tunnel ID

        Returns:
            True if deleted, False if not found
        """
        tunnel = self.tunnels.get(tunnel_id)
        if not tunnel:
            return False

        # Verify ownership
        from src.services.host_service import HostService
        host_service = HostService()
        host = await host_service.get_host(db, tunnel.host_id)
        if not host or host.user_id != user_id:
            return False

        # Stop tunnel if running
        if tunnel.forward_task:
            tunnel.forward_task.cancel()
            try:
                await tunnel.forward_task
            except asyncio.CancelledError:
                pass

        # Close SSH client
        if tunnel.ssh_client:
            tunnel.ssh_client.conn.close()

        # Remove from storage
        del self.tunnels[tunnel_id]
        if user_id in self.user_tunnels:
            self.user_tunnels[user_id].remove(tunnel_id)
            if not self.user_tunnels[user_id]:
                del self.user_tunnels[user_id]

        return True

    async def get_tunnel_status(
        self,
        db: AsyncSession,
        user_id: str,
        tunnel_id: str,
    ) -> TunnelStatusInfo:
        """Get tunnel status.

        Args:
            db: Database session
            user_id: User ID
            tunnel_id: Tunnel ID

        Returns:
            TunnelStatusInfo
        """
        tunnel = await self.get_tunnel(db, user_id, tunnel_id)
        if not tunnel:
            raise ValueError("Tunnel not found")

        tunnel_info = self.tunnels[tunnel_id]
        return TunnelStatusInfo(
            status=tunnel_info.status,
            connected=tunnel_info.connected,
            error=tunnel_info.error,
            last_error=tunnel_info.last_error,
            error_count=tunnel_info.error_count,
            last_connection_time=tunnel_info.last_connection_time,
            last_disconnection_time=tunnel_info.last_disconnection_time,
            uptime_seconds=tunnel_info.uptime_seconds,
        )

    async def start_tunnel(
        self,
        db: AsyncSession,
        user_id: str,
        tunnel_id: str,
        host: SSHHost,
        credential: Credential,
    ) -> bool:
        """Start tunnel connection.

        Args:
            db: Database session
            user_id: User ID
            tunnel_id: Tunnel ID
            host: SSH host
            credential: SSH credential

        Returns:
            True if started successfully
        """
        tunnel = self.tunnels.get(tunnel_id)
        if not tunnel:
            return False

        try:
            # Set status
            tunnel.status = TunnelStatus.CONNECTING
            tunnel.error = None

            # Create SSH client
            tunnel.ssh_client = await self.credential_service.get_ssh_client(db, host, credential)

            # Mark connected
            tunnel.status = TunnelStatus.CONNECTED
            tunnel.connected = True
            tunnel.error = None
            tunnel.error_count = 0
            tunnel.last_connection_time = datetime.utcnow().isoformat()
            tunnel.connection_start_time = asyncio.get_event_loop().time()

            return True
        except Exception as e:
            tunnel.status = TunnelStatus.FAILED
            tunnel.connected = False
            tunnel.error = str(e)
            tunnel.last_error = str(e)
            tunnel.error_count += 1
            tunnel.last_disconnection_time = datetime.utcnow().isoformat()
            return False

    async def stop_tunnel(
        self,
        user_id: str,
        tunnel_id: str,
    ) -> bool:
        """Stop tunnel connection.

        Args:
            user_id: User ID
            tunnel_id: Tunnel ID

        Returns:
            True if stopped successfully
        """
        tunnel = self.tunnels.get(tunnel_id)
        if not tunnel:
            return False

        try:
            # Cancel forward task
            if tunnel.forward_task:
                tunnel.forward_task.cancel()
                try:
                    await tunnel.forward_task
                except asyncio.CancelledError:
                    pass

            # Close SSH client
            if tunnel.ssh_client:
                tunnel.ssh_client.conn.close()

            # Update status
            tunnel.status = TunnelStatus.DISCONNECTED
            tunnel.connected = False
            tunnel.ssh_client = None
            tunnel.forward_task = None
            tunnel.connection_start_time = None
            tunnel.last_disconnection_time = datetime.utcnow().isoformat()

            return True
        except Exception as e:
            tunnel.error = str(e)
            tunnel.last_error = str(e)
            return False

    async def get_user_tunnels(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get summary of all user's tunnels.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with tunnel count and status summary
        """
        tunnels = await self.list_tunnels(db, user_id)

        status_summary = {
            "connected": 0,
            "disconnected": 0,
            "failed": 0,
            "connecting": 0,
        }

        for tunnel in tunnels:
            status_key = tunnel.status.lower()
            if status_key in status_summary:
                status_summary[status_key] += 1

        return {
            "total": len(tunnels),
            "status_summary": status_summary,
        }

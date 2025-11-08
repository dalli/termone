"""Tunnel manager for background tunnel lifecycle and auto-reconnection.

Handles:
- Background task management for active tunnels
- Auto-reconnection on connection loss
- Monitoring tunnel health
- Cleanup on application shutdown
"""

import asyncio
import logging
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.tunnel_service import TunnelService, TunnelStatus

logger = logging.getLogger(__name__)


class TunnelManager:
    """Manages tunnel lifecycle and auto-reconnection."""

    def __init__(self, tunnel_service: TunnelService):
        """Initialize tunnel manager.

        Args:
            tunnel_service: TunnelService instance
        """
        self.tunnel_service = tunnel_service
        self.active_tunnels: Dict[str, asyncio.Task] = {}
        self.reconnect_intervals: Dict[str, int] = {}  # tunnel_id -> reconnect interval (30s)
        self.max_reconnect_attempts = 5
        self.base_reconnect_interval = 30  # seconds

    async def start_tunnel_connection(
        self,
        db: AsyncSession,
        user_id: str,
        tunnel_id: str,
        host,
        credential,
    ) -> bool:
        """Start managing a tunnel connection.

        Args:
            db: Database session
            user_id: User ID
            tunnel_id: Tunnel ID
            host: SSH host
            credential: SSH credential

        Returns:
            True if started successfully
        """
        # Start tunnel
        success = await self.tunnel_service.start_tunnel(
            db, user_id, tunnel_id, host, credential
        )

        if success and self.tunnel_service.tunnels[tunnel_id].auto_reconnect:
            # Create background reconnection task
            task = asyncio.create_task(
                self._reconnect_loop(db, user_id, tunnel_id, host, credential)
            )
            self.active_tunnels[tunnel_id] = task

        return success

    async def stop_tunnel_connection(self, user_id: str, tunnel_id: str) -> bool:
        """Stop managing a tunnel connection.

        Args:
            user_id: User ID
            tunnel_id: Tunnel ID

        Returns:
            True if stopped successfully
        """
        # Stop tunnel
        success = await self.tunnel_service.stop_tunnel(user_id, tunnel_id)

        # Cancel reconnection task
        if tunnel_id in self.active_tunnels:
            task = self.active_tunnels[tunnel_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_tunnels[tunnel_id]

        if tunnel_id in self.reconnect_intervals:
            del self.reconnect_intervals[tunnel_id]

        return success

    async def _reconnect_loop(
        self,
        db: AsyncSession,
        user_id: str,
        tunnel_id: str,
        host,
        credential,
    ) -> None:
        """Background task for monitoring and reconnecting tunnel.

        Args:
            db: Database session
            user_id: User ID
            tunnel_id: Tunnel ID
            host: SSH host
            credential: SSH credential
        """
        reconnect_delay = self.base_reconnect_interval

        while True:
            try:
                # Sleep before checking
                await asyncio.sleep(reconnect_delay)

                tunnel = self.tunnel_service.tunnels.get(tunnel_id)
                if not tunnel:
                    break

                # Check if tunnel is still enabled
                if not tunnel.enabled or not tunnel.auto_reconnect:
                    break

                # Check if connection lost
                if not tunnel.connected or tunnel.status == TunnelStatus.FAILED:
                    logger.info(f"Reconnecting tunnel {tunnel_id}")

                    # Attempt reconnection
                    success = await self.tunnel_service.start_tunnel(
                        db, user_id, tunnel_id, host, credential
                    )

                    if success:
                        # Reset reconnect interval on success
                        reconnect_delay = self.base_reconnect_interval
                        tunnel.error_count = 0
                    else:
                        # Exponential backoff on failure
                        tunnel.status = TunnelStatus.RECONNECTING
                        if tunnel.error_count < self.max_reconnect_attempts:
                            reconnect_delay = min(
                                self.base_reconnect_interval * (2 ** tunnel.error_count),
                                300  # max 5 minutes
                            )
                        else:
                            # Stop trying after max attempts
                            tunnel.status = TunnelStatus.FAILED
                            break

            except asyncio.CancelledError:
                logger.debug(f"Reconnect loop cancelled for tunnel {tunnel_id}")
                break
            except Exception as e:
                logger.error(f"Error in reconnect loop for tunnel {tunnel_id}: {e}")
                # Continue trying after error
                await asyncio.sleep(reconnect_delay)

    async def shutdown(self) -> None:
        """Shutdown all tunnel connections gracefully."""
        logger.info(f"Shutting down {len(self.active_tunnels)} tunnels")

        tasks = list(self.active_tunnels.values())
        for task in tasks:
            task.cancel()

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # Close all SSH connections
        for tunnel in self.tunnel_service.tunnels.values():
            try:
                if tunnel.ssh_client:
                    tunnel.ssh_client.conn.close()
            except Exception as e:
                logger.error(f"Error closing tunnel {tunnel.id}: {e}")

        self.active_tunnels.clear()
        logger.info("All tunnels shut down")

    async def get_tunnel_health(self, tunnel_id: str) -> Optional[Dict]:
        """Get health status of a tunnel.

        Args:
            tunnel_id: Tunnel ID

        Returns:
            Dictionary with health information or None if not found
        """
        tunnel = self.tunnel_service.tunnels.get(tunnel_id)
        if not tunnel:
            return None

        return {
            "tunnel_id": tunnel_id,
            "status": tunnel.status.value,
            "connected": tunnel.connected,
            "error_count": tunnel.error_count,
            "uptime_seconds": tunnel.uptime_seconds,
            "last_error": tunnel.last_error,
            "auto_reconnect": tunnel.auto_reconnect,
            "reconnect_interval": self.reconnect_intervals.get(tunnel_id, self.base_reconnect_interval),
        }

    def get_active_tunnel_count(self) -> int:
        """Get count of active tunnels being managed.

        Returns:
            Number of active tunnels
        """
        return len([t for t in self.tunnel_service.tunnels.values() if t.connected])

    def get_tunnel_status_summary(self) -> Dict[str, int]:
        """Get summary of all tunnel statuses.

        Returns:
            Dictionary with status counts
        """
        summary = {
            "connected": 0,
            "disconnected": 0,
            "failed": 0,
            "connecting": 0,
            "reconnecting": 0,
        }

        for tunnel in self.tunnel_service.tunnels.values():
            status_key = tunnel.status.value.lower()
            if status_key in summary:
                summary[status_key] += 1

        return summary

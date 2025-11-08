"""Stats service for managing system statistics collection and caching."""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.infrastructure import SSHHost
from src.services.ssh_client import SSHClient
from src.services.credential_service import CredentialService
from src.services.stats_collector import StatsCollector
from src.exceptions import NotFoundException, PermissionException

logger = logging.getLogger(__name__)


class StatsService:
    """Service for managing system statistics collection."""

    def __init__(self, credential_service: CredentialService):
        """Initialize stats service.

        Args:
            credential_service: Credential service for accessing host credentials
        """
        self.credential_service = credential_service
        self.stats_cache: Dict[str, Any] = {}
        self.collection_tasks: Dict[str, asyncio.Task] = {}
        self.subscribers: Dict[str, list] = defaultdict(list)

    async def get_current_stats(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get current cached stats for a host.

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID

        Returns:
            Current stats snapshot

        Raises:
            NotFoundException: If host not found or no stats available
            PermissionException: If user doesn't have access
        """
        # Verify host exists and user has access
        from sqlalchemy import select

        result = await db.execute(
            select(SSHHost).where(SSHHost.id == host_id)
        )
        host = result.scalar_one_or_none()

        if not host:
            raise NotFoundException(resource="Host", identifier=host_id)

        if host.created_by_user_id != user_id:
            raise PermissionException(
                resource="Host",
                action="read_stats",
                reason="User does not own this host",
            )

        # Get cached stats
        if host_id not in self.stats_cache:
            raise NotFoundException(
                resource="StatsSnapshot",
                identifier=host_id,
            )

        return self.stats_cache[host_id]

    async def start_collection(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
        interval: int = 5,
    ) -> None:
        """Start background stats collection for a host.

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID
            interval: Collection interval in seconds
        """
        # Verify host exists and user has access
        from sqlalchemy import select

        result = await db.execute(
            select(SSHHost).where(SSHHost.id == host_id)
        )
        host = result.scalar_one_or_none()

        if not host:
            raise NotFoundException(resource="Host", identifier=host_id)

        if host.created_by_user_id != user_id:
            raise PermissionException(
                resource="Host",
                action="read_stats",
                reason="User does not own this host",
            )

        # If already collecting, don't start again
        if host_id in self.collection_tasks:
            return

        # Start collection task
        task = asyncio.create_task(
            self._collect_stats_loop(db, host_id, user_id, interval)
        )
        self.collection_tasks[host_id] = task

        logger.info(f"Started stats collection for host {host_id}")

    async def stop_collection(self, host_id: str) -> None:
        """Stop background stats collection for a host.

        Args:
            host_id: Host ID
        """
        if host_id in self.collection_tasks:
            task = self.collection_tasks[host_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.collection_tasks[host_id]

            logger.info(f"Stopped stats collection for host {host_id}")

    async def subscribe(
        self,
        host_id: str,
        callback,
    ) -> None:
        """Subscribe to stats updates for a host.

        Args:
            host_id: Host ID
            callback: Async callback function to receive stats
        """
        if host_id not in self.subscribers:
            self.subscribers[host_id] = []

        self.subscribers[host_id].append(callback)

    async def unsubscribe(
        self,
        host_id: str,
        callback,
    ) -> None:
        """Unsubscribe from stats updates for a host.

        Args:
            host_id: Host ID
            callback: Callback function to remove
        """
        if host_id in self.subscribers:
            try:
                self.subscribers[host_id].remove(callback)
            except ValueError:
                pass

    async def _collect_stats_loop(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
        interval: int,
    ) -> None:
        """Background loop for collecting stats.

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID
            interval: Collection interval in seconds
        """
        from sqlalchemy import select

        try:
            while True:
                try:
                    # Get host and credential
                    result = await db.execute(
                        select(SSHHost).where(SSHHost.id == host_id)
                    )
                    host = result.scalar_one_or_none()

                    if not host:
                        logger.warning(f"Host {host_id} not found, stopping collection")
                        break

                    credential = await self.credential_service.get_host_credential(
                        db, host_id
                    )
                    if not credential:
                        logger.warning(
                            f"No credential for host {host_id}, stopping collection"
                        )
                        break

                    # Decrypt credential and create SSH client
                    credential_value = (
                        await self.credential_service.decrypt_credential(credential)
                    )

                    async with SSHClient(
                        hostname=host.hostname,
                        port=host.port,
                        username=host.username,
                        password=credential_value
                        if credential.credential_type == "password"
                        else None,
                        private_key=credential_value
                        if credential.credential_type == "ssh_key"
                        else None,
                    ) as ssh_client:
                        # Collect stats
                        collector = StatsCollector(ssh_client)
                        stats = await collector.collect_all_stats()

                        # Cache stats
                        self.stats_cache[host_id] = stats

                        # Notify subscribers
                        if host_id in self.subscribers:
                            for callback in self.subscribers[host_id]:
                                try:
                                    await callback(stats)
                                except Exception as e:
                                    logger.error(f"Error calling stats callback: {e}")

                except Exception as e:
                    logger.error(f"Error collecting stats for host {host_id}: {e}")

                # Wait for next interval
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info(f"Stats collection cancelled for host {host_id}")
        except Exception as e:
            logger.error(f"Error in stats collection loop for host {host_id}: {e}")
        finally:
            # Clean up
            if host_id in self.collection_tasks:
                del self.collection_tasks[host_id]

    def get_cached_stats(self, host_id: str) -> Optional[Dict[str, Any]]:
        """Get cached stats for a host without permission checks.

        Args:
            host_id: Host ID

        Returns:
            Cached stats or None
        """
        return self.stats_cache.get(host_id)

    async def cleanup_all(self) -> None:
        """Clean up all collection tasks."""
        for host_id in list(self.collection_tasks.keys()):
            await self.stop_collection(host_id)

        self.stats_cache.clear()
        self.subscribers.clear()

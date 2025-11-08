"""Terminal session management service."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4

import asyncssh
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.infrastructure import SSHHost
from src.models.session import TerminalSession
from src.services.ssh_client import SSHClient
from src.services.credential_service import CredentialService
from src.exceptions import NotFoundException, ValidationException, PermissionException

logger = logging.getLogger(__name__)


class TerminalSessionService:
    """Service for managing terminal sessions."""

    def __init__(self, credential_service: CredentialService):
        """Initialize terminal session service."""
        self.credential_service = credential_service
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.cleanup_tasks: Dict[str, asyncio.Task] = {}

    async def create_session(
        self,
        db: AsyncSession,
        host_id: str,
        user_id: str,
        rows: int = 24,
        cols: int = 80,
        env: Optional[Dict[str, str]] = None,
    ) -> TerminalSession:
        """Create a new terminal session.

        Args:
            db: Database session
            host_id: Host ID
            user_id: User ID
            rows: Terminal rows
            cols: Terminal columns
            env: Environment variables

        Returns:
            TerminalSession object

        Raises:
            NotFoundException: If host not found
            PermissionException: If user cannot access host
            ValidationException: If session creation fails
        """
        # Get host
        result = await db.execute(
            select(SSHHost).where(SSHHost.id == host_id)
        )
        host = result.scalar_one_or_none()

        if not host:
            raise NotFoundException(resource="Host", identifier=host_id)

        if host.created_by_user_id != user_id:
            raise PermissionException(
                resource="Host",
                action="terminal_access",
                reason="User does not own this host",
            )

        # Get credential
        credential = await self.credential_service.get_host_credential(db, host_id)
        if not credential:
            raise ValidationException(
                field="host_id",
                message="No credential configured for host",
                code="NO_CREDENTIAL",
            )

        # Decrypt credential
        credential_value = await self.credential_service.decrypt_credential(credential)

        # Create SSH client
        ssh_client = SSHClient(
            hostname=host.hostname,
            port=host.port,
            username=host.username,
            password=credential_value if credential.credential_type == "password" else None,
            private_key=credential_value if credential.credential_type == "ssh_key" else None,
        )

        # Connect to SSH server
        try:
            await ssh_client.connect()
        except Exception as e:
            raise ValidationException(
                field="host_id",
                message=f"Failed to connect to host: {str(e)}",
                code="CONNECTION_FAILED",
            )

        # Create database record
        session_id = str(uuid4())
        terminal_session = TerminalSession(
            id=session_id,
            host_id=host_id,
            user_id=user_id,
            rows=rows,
            cols=cols,
            status="created",
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        db.add(terminal_session)
        await db.commit()
        await db.refresh(terminal_session)

        # Store in-memory session data
        self.sessions[session_id] = {
            "session": terminal_session,
            "ssh_client": ssh_client,
            "process": None,
            "rows": rows,
            "cols": cols,
            "env": env or {},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }

        # Start cleanup task
        self._schedule_cleanup(session_id)

        logger.info(f"Terminal session created: {session_id} on host {host_id}")
        return terminal_session

    async def get_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> TerminalSession:
        """Get terminal session.

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID

        Returns:
            TerminalSession object

        Raises:
            NotFoundException: If session not found
            PermissionException: If user doesn't own session
        """
        result = await db.execute(
            select(TerminalSession).where(TerminalSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundException(resource="TerminalSession", identifier=session_id)

        if session.user_id != user_id:
            raise PermissionException(
                resource="TerminalSession",
                action="read",
                reason="User does not own this session",
            )

        return session

    async def list_sessions(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> list:
        """List all terminal sessions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of TerminalSession objects
        """
        result = await db.execute(
            select(TerminalSession).where(TerminalSession.user_id == user_id)
        )
        return result.scalars().all()

    async def spawn_pty(
        self,
        session_id: str,
    ) -> asyncssh.SSHClientProcess:
        """Spawn a PTY for a session.

        Args:
            session_id: Session ID

        Returns:
            SSH process

        Raises:
            NotFoundException: If session not found
        """
        if session_id not in self.sessions:
            raise NotFoundException(resource="TerminalSession", identifier=session_id)

        session_data = self.sessions[session_id]
        ssh_client = session_data["ssh_client"]

        # Spawn PTY
        process = await ssh_client.spawn_pty(
            rows=session_data["rows"],
            cols=session_data["cols"],
        )

        session_data["process"] = process
        return process

    async def resize_terminal(
        self,
        session_id: str,
        rows: int,
        cols: int,
    ) -> bool:
        """Resize terminal.

        Args:
            session_id: Session ID
            rows: New rows
            cols: New columns

        Returns:
            True if successful

        Raises:
            NotFoundException: If session not found
        """
        if session_id not in self.sessions:
            raise NotFoundException(resource="TerminalSession", identifier=session_id)

        session_data = self.sessions[session_id]
        process = session_data.get("process")

        if not process:
            return False

        ssh_client = session_data["ssh_client"]
        success = await ssh_client.set_terminal_size(process, rows, cols)

        if success:
            session_data["rows"] = rows
            session_data["cols"] = cols

        return success

    async def update_activity(
        self,
        session_id: str,
    ) -> None:
        """Update last activity timestamp.

        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = datetime.utcnow()

    async def close_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> bool:
        """Close a terminal session.

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID

        Returns:
            True if closed successfully

        Raises:
            NotFoundException: If session not found
            PermissionException: If user doesn't own session
        """
        # Get session record
        terminal_session = await self.get_session(db, session_id, user_id)

        # Close SSH connection
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            ssh_client = session_data["ssh_client"]

            await ssh_client.close()

            # Cancel cleanup task
            if session_id in self.cleanup_tasks:
                self.cleanup_tasks[session_id].cancel()
                del self.cleanup_tasks[session_id]

            del self.sessions[session_id]

        # Update database record
        terminal_session.status = "closed"
        terminal_session.last_activity = datetime.utcnow()

        db.add(terminal_session)
        await db.commit()

        logger.info(f"Terminal session closed: {session_id}")
        return True

    def _schedule_cleanup(self, session_id: str, timeout: int = 300) -> None:
        """Schedule session cleanup after timeout.

        Args:
            session_id: Session ID
            timeout: Timeout in seconds (default 5 minutes)
        """
        async def cleanup():
            try:
                await asyncio.sleep(timeout)
                if session_id in self.sessions:
                    logger.info(f"Cleaning up inactive session: {session_id}")
                    session_data = self.sessions[session_id]
                    ssh_client = session_data["ssh_client"]
                    await ssh_client.close()
                    del self.sessions[session_id]
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")

        task = asyncio.create_task(cleanup())
        self.cleanup_tasks[session_id] = task

    def get_session_data(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get in-memory session data.

        Args:
            session_id: Session ID

        Returns:
            Session data or None
        """
        return self.sessions.get(session_id)

    async def cleanup_all(self) -> None:
        """Clean up all sessions."""
        for session_id in list(self.sessions.keys()):
            try:
                session_data = self.sessions[session_id]
                ssh_client = session_data["ssh_client"]
                await ssh_client.close()

                if session_id in self.cleanup_tasks:
                    self.cleanup_tasks[session_id].cancel()
                    del self.cleanup_tasks[session_id]

                del self.sessions[session_id]
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {e}")

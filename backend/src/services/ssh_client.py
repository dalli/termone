"""SSH client wrapper for managing SSH connections."""

import asyncio
import logging
from typing import Optional, Tuple, BinaryIO
from uuid import uuid4

import asyncssh

from src.exceptions import ValidationException, NotFoundException

logger = logging.getLogger(__name__)


class SSHClient:
    """Async SSH client wrapper for terminal and SFTP operations."""

    def __init__(
        self,
        hostname: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """Initialize SSH client.

        Args:
            hostname: SSH host
            port: SSH port
            username: SSH username
            password: SSH password (optional)
            private_key: SSH private key (optional)
            timeout: Connection timeout in seconds
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.timeout = timeout
        self.connection: Optional[asyncssh.SSHClientConnection] = None
        self.id = str(uuid4())

    async def connect(self) -> bool:
        """Establish SSH connection.

        Returns:
            True if connection successful

        Raises:
            ValidationException: If credentials invalid
            ConnectionError: If connection fails
        """
        if not self.hostname or not self.username:
            raise ValidationException(
                field="credentials",
                message="Hostname and username required",
                code="INVALID_CREDENTIALS",
            )

        try:
            # Prepare connection options
            known_hosts = None  # Don't check known_hosts for now

            if self.private_key:
                # Use private key
                try:
                    key = asyncssh.import_private_key(self.private_key)
                    self.connection = await asyncio.wait_for(
                        asyncssh.connect(
                            self.hostname,
                            port=self.port,
                            username=self.username,
                            client_keys=[key],
                            known_hosts=known_hosts,
                        ),
                        timeout=self.timeout,
                    )
                except (ValueError, asyncssh.KeyImportError) as e:
                    raise ValidationException(
                        field="private_key",
                        message="Invalid SSH key",
                        code="INVALID_KEY",
                    )
            elif self.password:
                # Use password
                self.connection = await asyncio.wait_for(
                    asyncssh.connect(
                        self.hostname,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        known_hosts=known_hosts,
                    ),
                    timeout=self.timeout,
                )
            else:
                raise ValidationException(
                    field="credentials",
                    message="Password or private key required",
                    code="NO_CREDENTIALS",
                )

            logger.info(f"SSH connection established to {self.hostname}")
            return True

        except asyncio.TimeoutError:
            raise ConnectionError(f"SSH connection timeout to {self.hostname}")
        except asyncssh.PermissionDenied:
            raise ValidationException(
                field="credentials",
                message="Authentication failed",
                code="AUTH_FAILED",
            )
        except (asyncssh.Error, OSError) as e:
            raise ConnectionError(f"SSH connection failed: {str(e)}")

    async def spawn_pty(
        self,
        term_type: str = "xterm",
        rows: int = 24,
        cols: int = 80,
    ) -> asyncssh.SSHClientProcess:
        """Spawn a PTY (pseudo-terminal) shell.

        Args:
            term_type: Terminal type (xterm, linux, etc.)
            rows: Terminal rows
            cols: Terminal columns

        Returns:
            SSH process with PTY

        Raises:
            ConnectionError: If not connected
        """
        if not self.connection:
            raise ConnectionError("Not connected to SSH server")

        try:
            process = await self.connection.create_session(
                asyncssh.process.SSHClientProcess,
                term_type=term_type,
                term_size=(cols, rows),
            )
            logger.info(f"PTY spawned: {term_type} {cols}x{rows}")
            return process
        except asyncssh.Error as e:
            raise ConnectionError(f"Failed to spawn PTY: {str(e)}")

    async def execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
    ) -> Tuple[str, str, int]:
        """Execute a command on remote server.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Tuple of (stdout, stderr, exit_code)

        Raises:
            ConnectionError: If not connected
        """
        if not self.connection:
            raise ConnectionError("Not connected to SSH server")

        try:
            result = await asyncio.wait_for(
                self.connection.run(command),
                timeout=timeout or self.timeout,
            )
            return (result.stdout or "", result.stderr or "", result.exit_status)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Command execution timeout: {command}")
        except asyncssh.Error as e:
            raise ConnectionError(f"Command execution failed: {str(e)}")

    async def set_terminal_size(
        self,
        process: asyncssh.SSHClientProcess,
        rows: int,
        cols: int,
    ) -> bool:
        """Resize terminal.

        Args:
            process: SSH process
            rows: New rows
            cols: New columns

        Returns:
            True if successful
        """
        try:
            process.set_terminal_size(cols, rows)
            return True
        except asyncssh.Error as e:
            logger.error(f"Failed to resize terminal: {e}")
            return False

    async def close(self) -> None:
        """Close SSH connection."""
        if self.connection:
            try:
                self.connection.close()
                await self.connection.wait_closed()
                logger.info(f"SSH connection closed: {self.hostname}")
            except Exception as e:
                logger.error(f"Error closing SSH connection: {e}")
            finally:
                self.connection = None

    def is_connected(self) -> bool:
        """Check if connected.

        Returns:
            True if connected
        """
        return self.connection is not None and not self.connection.is_closed()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

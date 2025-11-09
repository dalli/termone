"""SFTP client wrapper for async file operations.

Provides async SFTP operations:
- List directory contents
- Upload files
- Download files
- Read/write file content
- Change permissions
- Delete files
- Move/rename files
"""

import asyncio
import os
import stat
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncssh

from src.services.ssh_client import SSHClient


class FileInfo:
    """File information from SFTP stat."""

    def __init__(self, name: str, attrs: asyncssh.SFTPAttrs):
        self.name = name
        self.size = attrs.size or 0
        self.mode = attrs.permissions or 0o644
        self.mtime = attrs.mtime or 0
        self.owner_uid = attrs.uid or 0
        self.owner_gid = attrs.gid or 0

    @property
    def type(self) -> str:
        """Determine file type from mode."""
        if stat.S_ISDIR(self.mode):
            return "directory"
        elif stat.S_ISLNK(self.mode):
            return "symlink"
        else:
            return "file"

    @property
    def modified(self) -> str:
        """Format modification time as ISO string."""
        if self.mtime:
            return datetime.fromtimestamp(self.mtime).isoformat()
        return ""

    @property
    def owner(self) -> str:
        """Format owner as uid:gid."""
        return f"{self.owner_uid}:{self.owner_gid}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "mode": self.mode,
            "modified": self.modified,
            "owner": self.owner,
        }


class SFTPClient:
    """Async SFTP client wrapper."""

    def __init__(self, ssh_client: SSHClient):
        """Initialize SFTP client with SSH connection.

        Args:
            ssh_client: Connected SSHClient instance
        """
        self.ssh_client = ssh_client
        self.conn = ssh_client.conn
        self._sftp_client: Optional[asyncssh.SFTPClient] = None

    async def __aenter__(self):
        """Context manager entry."""
        await self._ensure_sftp()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def _ensure_sftp(self):
        """Ensure SFTP client is open."""
        if self._sftp_client is None:
            self._sftp_client = await self.conn.start_sftp_client()

    async def close(self):
        """Close SFTP client."""
        if self._sftp_client:
            self._sftp_client.exit()
            await self._sftp_client.wait_closed()
            self._sftp_client = None

    async def list_dir(self, path: str = ".") -> List[FileInfo]:
        """List directory contents.

        Args:
            path: Directory path to list (default: current directory)

        Returns:
            List of FileInfo objects
        """
        await self._ensure_sftp()

        entries = []
        try:
            # List directory with attributes
            dir_listing = await self._sftp_client.listdir_attr(path)
            for item in dir_listing:
                entries.append(FileInfo(item.filename, item))
        except asyncssh.SFTPError as e:
            # If path is not a directory or doesn't exist, return empty list
            if "not a directory" in str(e) or "no such file" in str(e):
                return []
            raise

        return entries

    async def open_file(
        self,
        path: str,
        mode: str = "r",
        encoding: str = "utf-8"
    ) -> str:
        """Read file content.

        Args:
            path: File path to read
            mode: File mode (default: "r" for read)
            encoding: Text encoding (default: "utf-8")

        Returns:
            File content as string
        """
        await self._ensure_sftp()

        # Read with size limit to prevent large file issues
        max_size = 10 * 1024 * 1024  # 10 MB limit
        try:
            async with self._sftp_client.open(path, mode) as f:
                data = await f.read(max_size)
                if isinstance(data, bytes):
                    return data.decode(encoding)
                return data
        except asyncssh.SFTPError as e:
            if "no such file" in str(e):
                raise FileNotFoundError(f"File not found: {path}")
            raise

    async def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8"
    ) -> None:
        """Write content to file.

        Args:
            path: File path to write
            content: Content to write
            encoding: Text encoding (default: "utf-8")
        """
        await self._ensure_sftp()

        try:
            async with self._sftp_client.open(path, "w") as f:
                data = content.encode(encoding) if isinstance(content, str) else content
                await f.write(data)
        except asyncssh.SFTPError as e:
            if "permission denied" in str(e):
                raise PermissionError(f"Permission denied: {path}")
            raise

    async def download_file(self, remote_path: str, local_path: str) -> int:
        """Download file from remote to local.

        Args:
            remote_path: Remote file path
            local_path: Local file path to save to

        Returns:
            Number of bytes downloaded
        """
        await self._ensure_sftp()

        try:
            bytes_downloaded = await self._sftp_client.get(remote_path, local_path)
            return bytes_downloaded or 0
        except asyncssh.SFTPError as e:
            if "no such file" in str(e):
                raise FileNotFoundError(f"Remote file not found: {remote_path}")
            raise

    async def upload_file(self, local_path: str, remote_path: str) -> int:
        """Upload file from local to remote.

        Args:
            local_path: Local file path
            remote_path: Remote file path to save to

        Returns:
            Number of bytes uploaded
        """
        await self._ensure_sftp()

        try:
            bytes_uploaded = await self._sftp_client.put(local_path, remote_path)
            return bytes_uploaded or 0
        except asyncssh.SFTPError as e:
            if "permission denied" in str(e):
                raise PermissionError(f"Permission denied: {remote_path}")
            if "no such file" in str(e):
                raise FileNotFoundError(f"Cannot write to {remote_path}")
            raise

    async def stat(self, path: str) -> FileInfo:
        """Get file statistics.

        Args:
            path: File path

        Returns:
            FileInfo object
        """
        await self._ensure_sftp()

        try:
            attrs = await self._sftp_client.stat(path)
            return FileInfo(os.path.basename(path), attrs)
        except asyncssh.SFTPError as e:
            if "no such file" in str(e):
                raise FileNotFoundError(f"File not found: {path}")
            raise

    async def chmod(self, path: str, mode: int) -> None:
        """Change file permissions.

        Args:
            path: File path
            mode: New permissions (octal, e.g., 0o644)
        """
        await self._ensure_sftp()

        try:
            await self._sftp_client.chmod(path, mode)
        except asyncssh.SFTPError as e:
            if "permission denied" in str(e):
                raise PermissionError(f"Permission denied: {path}")
            if "no such file" in str(e):
                raise FileNotFoundError(f"File not found: {path}")
            raise

    async def delete(self, path: str) -> None:
        """Delete a file.

        Args:
            path: File path to delete
        """
        await self._ensure_sftp()

        try:
            await self._sftp_client.remove(path)
        except asyncssh.SFTPError as e:
            if "permission denied" in str(e):
                raise PermissionError(f"Permission denied: {path}")
            if "no such file" in str(e):
                raise FileNotFoundError(f"File not found: {path}")
            raise

    async def mkdir(self, path: str, mode: int = 0o755) -> None:
        """Create directory.

        Args:
            path: Directory path
            mode: Directory permissions (default: 0o755)
        """
        await self._ensure_sftp()

        try:
            await self._sftp_client.mkdir(path, mode)
        except asyncssh.SFTPError as e:
            if "permission denied" in str(e):
                raise PermissionError(f"Permission denied: {path}")
            if "already exists" in str(e):
                raise FileExistsError(f"Directory already exists: {path}")
            raise

    async def rmdir(self, path: str) -> None:
        """Remove directory.

        Args:
            path: Directory path
        """
        await self._ensure_sftp()

        try:
            await self._sftp_client.rmdir(path)
        except asyncssh.SFTPError as e:
            if "permission denied" in str(e):
                raise PermissionError(f"Permission denied: {path}")
            if "no such file" in str(e):
                raise FileNotFoundError(f"Directory not found: {path}")
            raise

    async def rename(self, oldpath: str, newpath: str) -> None:
        """Rename or move file.

        Args:
            oldpath: Current file path
            newpath: New file path
        """
        await self._ensure_sftp()

        try:
            await self._sftp_client.rename(oldpath, newpath)
        except asyncssh.SFTPError as e:
            if "permission denied" in str(e):
                raise PermissionError(f"Permission denied: {oldpath}")
            if "no such file" in str(e):
                raise FileNotFoundError(f"File not found: {oldpath}")
            raise

    async def exists(self, path: str) -> bool:
        """Check if file or directory exists.

        Args:
            path: File path

        Returns:
            True if path exists, False otherwise
        """
        await self._ensure_sftp()

        try:
            await self._sftp_client.stat(path)
            return True
        except asyncssh.SFTPError:
            return False

    async def is_dir(self, path: str) -> bool:
        """Check if path is directory.

        Args:
            path: File path

        Returns:
            True if path is directory, False otherwise
        """
        await self._ensure_sftp()

        try:
            attrs = await self._sftp_client.stat(path)
            return stat.S_ISDIR(attrs.permissions or 0)
        except asyncssh.SFTPError:
            return False

    async def is_file(self, path: str) -> bool:
        """Check if path is regular file.

        Args:
            path: File path

        Returns:
            True if path is regular file, False otherwise
        """
        await self._ensure_sftp()

        try:
            attrs = await self._sftp_client.stat(path)
            return stat.S_ISREG(attrs.permissions or 0)
        except asyncssh.SFTPError:
            return False

    async def get_file_size(self, path: str) -> int:
        """Get file size in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes
        """
        await self._ensure_sftp()

        try:
            attrs = await self._sftp_client.stat(path)
            return attrs.size or 0
        except asyncssh.SFTPError as e:
            if "no such file" in str(e):
                raise FileNotFoundError(f"File not found: {path}")
            raise

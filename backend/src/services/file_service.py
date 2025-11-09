"""File service for SFTP operations.

Provides high-level file operations:
- List directories with permission checks
- Upload and download files
- Read and write file content
- Change file permissions
- Delete files and directories
- Move/rename files
"""

import os
import tempfile
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Credential, SSHHost
from src.services.credential_service import CredentialService
from src.services.sftp_client import SFTPClient
from src.services.ssh_client import SSHClient


class FileService:
    """High-level file service for SFTP operations."""

    def __init__(self, credential_service: CredentialService):
        """Initialize file service.

        Args:
            credential_service: Credential service for credential decryption
        """
        self.credential_service = credential_service

    async def _get_sftp_client(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential
    ) -> SFTPClient:
        """Create and connect SFTP client.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential

        Returns:
            Connected SFTPClient instance
        """
        # Get SSH client
        ssh_client = await self.credential_service.get_ssh_client(
            db, host, credential
        )

        return SFTPClient(ssh_client)

    async def list_directory(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str = "."
    ) -> List[Dict[str, Any]]:
        """List directory contents.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: Directory path to list

        Returns:
            List of file info dictionaries
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                entries = await sftp.list_dir(path)
                return [entry.to_dict() for entry in entries]
        except Exception as e:
            raise RuntimeError(f"Failed to list directory {path}: {str(e)}")

    async def upload_file(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        local_path: str,
        remote_path: str
    ) -> Dict[str, Any]:
        """Upload file to remote host.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            local_path: Local file path
            remote_path: Remote file path

        Returns:
            Upload result with size and path
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                bytes_uploaded = await sftp.upload_file(local_path, remote_path)
                return {
                    "path": remote_path,
                    "size": bytes_uploaded,
                    "message": f"File uploaded successfully ({bytes_uploaded} bytes)"
                }
        except PermissionError as e:
            raise PermissionError(f"Permission denied for upload: {str(e)}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to upload file: {str(e)}")

    async def download_file(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        remote_path: str
    ) -> bytes:
        """Download file from remote host.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            remote_path: Remote file path

        Returns:
            File content as bytes
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                # Create temporary file for download
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = tmp.name

                try:
                    await sftp.download_file(remote_path, tmp_path)
                    with open(tmp_path, "rb") as f:
                        return f.read()
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Remote file not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to download file: {str(e)}")

    async def read_file(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str,
        encoding: str = "utf-8"
    ) -> str:
        """Read file content.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: File path
            encoding: Text encoding (default: utf-8)

        Returns:
            File content as string
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                return await sftp.open_file(path, mode="r", encoding=encoding)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {str(e)}")

    async def write_file(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str,
        content: str,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """Write content to file.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: File path
            content: Content to write
            encoding: Text encoding (default: utf-8)

        Returns:
            Write result
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                await sftp.write_file(path, content, encoding=encoding)
                # Get file info after write
                file_info = await sftp.stat(path)
                return {
                    "path": path,
                    "size": file_info.size,
                    "mode": file_info.mode,
                    "message": f"File written successfully"
                }
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to write file: {str(e)}")

    async def delete_file(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str
    ) -> Dict[str, Any]:
        """Delete file.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: File path

        Returns:
            Deletion result
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                await sftp.delete(path)
                return {
                    "path": path,
                    "message": "File deleted successfully"
                }
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {str(e)}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete file: {str(e)}")

    async def chmod_file(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str,
        mode: int
    ) -> Dict[str, Any]:
        """Change file permissions.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: File path
            mode: New permissions (octal, e.g., 644)

        Returns:
            Chmod result
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                await sftp.chmod(path, mode)
                file_info = await sftp.stat(path)
                return {
                    "path": path,
                    "mode": file_info.mode,
                    "message": f"Permissions changed successfully to {oct(mode)}"
                }
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {str(e)}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to change permissions: {str(e)}")

    async def rename_file(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        old_path: str,
        new_path: str
    ) -> Dict[str, Any]:
        """Rename or move file.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            old_path: Current file path
            new_path: New file path

        Returns:
            Rename result
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                await sftp.rename(old_path, new_path)
                file_info = await sftp.stat(new_path)
                return {
                    "old_path": old_path,
                    "new_path": new_path,
                    "size": file_info.size,
                    "message": "File renamed successfully"
                }
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {str(e)}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to rename file: {str(e)}")

    async def create_directory(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str,
        mode: int = 0o755
    ) -> Dict[str, Any]:
        """Create directory.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: Directory path
            mode: Directory permissions (default: 0o755)

        Returns:
            Directory creation result
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                await sftp.mkdir(path, mode)
                return {
                    "path": path,
                    "mode": mode,
                    "message": "Directory created successfully"
                }
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {str(e)}")
        except FileExistsError as e:
            raise FileExistsError(f"Directory already exists: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to create directory: {str(e)}")

    async def delete_directory(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str
    ) -> Dict[str, Any]:
        """Delete empty directory.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: Directory path

        Returns:
            Deletion result
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                await sftp.rmdir(path)
                return {
                    "path": path,
                    "message": "Directory deleted successfully"
                }
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {str(e)}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Directory not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete directory: {str(e)}")

    async def get_file_info(
        self,
        db: AsyncSession,
        host: SSHHost,
        credential: Credential,
        path: str
    ) -> Dict[str, Any]:
        """Get file information.

        Args:
            db: Database session
            host: SSH host
            credential: SSH credential
            path: File path

        Returns:
            File information dictionary
        """
        sftp = await self._get_sftp_client(db, host, credential)
        try:
            async with sftp:
                file_info = await sftp.stat(path)
                return file_info.to_dict()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to get file info: {str(e)}")

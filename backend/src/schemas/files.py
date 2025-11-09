"""Pydantic schemas for file operations."""

from typing import List, Optional

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """File information from directory listing."""

    name: str = Field(..., description="File name")
    type: str = Field(..., description="File type: file, directory, symlink")
    size: int = Field(..., description="File size in bytes")
    mode: int = Field(..., description="File permissions (octal)")
    modified: str = Field(..., description="Modification time (ISO format)")
    owner: str = Field(..., description="Owner as uid:gid")


class DirectoryListing(BaseModel):
    """Directory listing response."""

    entries: List[FileInfo] = Field(..., description="List of files in directory")
    path: Optional[str] = Field(None, description="Listed directory path")


class FileContent(BaseModel):
    """File content for read/write operations."""

    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    encoding: Optional[str] = Field("utf-8", description="Text encoding")
    mode: Optional[str] = Field("r", description="File mode: r (read) or w (write)")


class UploadRequest(BaseModel):
    """File upload request metadata."""

    path: str = Field(..., description="Destination directory path")
    overwrite: Optional[bool] = Field(False, description="Overwrite if exists")


class UploadResponse(BaseModel):
    """File upload response."""

    path: str = Field(..., description="Uploaded file path")
    size: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Upload status message")


class DownloadRequest(BaseModel):
    """File download request."""

    path: str = Field(..., description="Remote file path to download")


class EditRequest(BaseModel):
    """File edit request."""

    path: str = Field(..., description="File path")
    content: str = Field(..., description="New content")
    encoding: Optional[str] = Field("utf-8", description="Text encoding")
    create_if_missing: Optional[bool] = Field(True, description="Create if doesn't exist")


class EditResponse(BaseModel):
    """File edit response."""

    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    mode: int = Field(..., description="File permissions")
    message: str = Field(..., description="Edit status message")


class ChmodRequest(BaseModel):
    """File permission change request."""

    path: str = Field(..., description="File path")
    mode: int = Field(..., description="New permissions (octal, e.g., 644)")


class ChmodResponse(BaseModel):
    """File permission change response."""

    path: str = Field(..., description="File path")
    mode: int = Field(..., description="New permissions")
    message: str = Field(..., description="Chmod status message")


class DeleteRequest(BaseModel):
    """File delete request."""

    path: str = Field(..., description="File path to delete")


class DeleteResponse(BaseModel):
    """File delete response."""

    path: str = Field(..., description="Deleted file path")
    message: str = Field(..., description="Delete status message")


class MoveRequest(BaseModel):
    """File move/rename request."""

    old_path: str = Field(..., description="Current file path")
    new_path: str = Field(..., description="New file path")


class MoveResponse(BaseModel):
    """File move/rename response."""

    old_path: str = Field(..., description="Old file path")
    new_path: str = Field(..., description="New file path")
    size: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Move status message")


class MkdirRequest(BaseModel):
    """Directory create request."""

    path: str = Field(..., description="Directory path")
    mode: Optional[int] = Field(0o755, description="Directory permissions")


class MkdirResponse(BaseModel):
    """Directory create response."""

    path: str = Field(..., description="Directory path")
    mode: int = Field(..., description="Directory permissions")
    message: str = Field(..., description="Create status message")


class FileOperationError(BaseModel):
    """File operation error response."""

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    path: Optional[str] = Field(None, description="File path if applicable")

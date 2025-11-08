"""Pydantic schemas for hosts API."""

from typing import Optional, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class CredentialType(str, Enum):
    """Supported credential types."""

    PASSWORD = "password"
    SSH_KEY = "ssh_key"


class CredentialCreate(BaseModel):
    """Credential creation schema."""

    type: CredentialType = Field(..., description="Credential type")
    value: str = Field(..., description="Encrypted credential value")


class CredentialResponse(BaseModel):
    """Credential response schema (without value)."""

    id: str = Field(..., description="Credential ID")
    type: CredentialType = Field(..., description="Credential type")
    # Note: The actual encrypted value is never returned to the client

    class Config:
        from_attributes = True


class HostCreate(BaseModel):
    """Host creation schema."""

    hostname: str = Field(..., min_length=1, max_length=255, description="Hostname or IP address")
    port: int = Field(22, ge=1, le=65535, description="SSH port")
    username: str = Field(..., min_length=1, max_length=255, description="SSH username")
    tags: List[str] = Field(default_factory=list, description="Host tags for organization")
    folder: Optional[str] = Field(None, max_length=255, description="Folder for organizing hosts")
    credential: CredentialCreate = Field(..., description="SSH credential")
    description: Optional[str] = Field(None, max_length=1024, description="Host description")
    custom_port: Optional[int] = Field(None, ge=1, le=65535, description="Custom port override")

    @validator("hostname")
    def validate_hostname(cls, v):
        """Validate hostname format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Hostname cannot be empty")
        return v.strip()

    @validator("tags", pre=True, always=True)
    def validate_tags(cls, v):
        """Validate and normalize tags."""
        if v is None:
            return []
        return [tag.strip().lower() for tag in v if tag.strip()]


class HostUpdate(BaseModel):
    """Host update schema."""

    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    tags: Optional[List[str]] = Field(None)
    folder: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    is_active: Optional[bool] = Field(None)
    credential: Optional[CredentialCreate] = Field(None)

    class Config:
        # Allow partial updates
        extra = "ignore"


class HostResponse(BaseModel):
    """Host response schema."""

    host_id: str = Field(..., description="Unique host ID")
    hostname: str = Field(..., description="Hostname or IP address")
    port: int = Field(..., description="SSH port")
    username: str = Field(..., description="SSH username")
    tags: List[str] = Field(..., description="Host tags")
    folder: Optional[str] = Field(None, description="Host folder")
    description: Optional[str] = Field(None, description="Host description")
    is_active: bool = Field(..., description="Host availability status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by_user_id: str = Field(..., description="User who created this host")
    last_accessed: Optional[datetime] = Field(None, description="Last access time")
    credential_type: Optional[CredentialType] = Field(None, description="Type of credential configured")
    # Do not return encrypted credential value

    class Config:
        from_attributes = True


class HostListResponse(BaseModel):
    """Host list response for paginated results."""

    items: List[HostResponse] = Field(..., description="List of hosts")
    total: int = Field(..., ge=0, description="Total number of hosts")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Page size")

    class Config:
        from_attributes = True


class HostStatusResponse(BaseModel):
    """Host status response."""

    host_id: str = Field(..., description="Host ID")
    hostname: str = Field(..., description="Hostname")
    is_online: bool = Field(..., description="Whether host is currently reachable")
    last_checked: datetime = Field(..., description="Last status check time")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if offline")

    class Config:
        from_attributes = True


class PublicKeyDeployRequest(BaseModel):
    """Request to deploy public key to host."""

    public_key: str = Field(..., min_length=1, description="Public key to deploy")
    username: Optional[str] = Field(None, description="Override username for deployment")

    @validator("public_key")
    def validate_public_key(cls, v):
        """Validate SSH public key format."""
        if not v.startswith(("ssh-rsa", "ssh-ed25519", "ecdsa-sha2")):
            raise ValueError("Invalid SSH public key format")
        return v


class PublicKeyDeployResponse(BaseModel):
    """Response from public key deployment."""

    host_id: str = Field(..., description="Host ID")
    status: str = Field(..., description="Deployment status (success/failed/pending)")
    message: Optional[str] = Field(None, description="Status message")
    deployment_id: Optional[str] = Field(None, description="Deployment task ID")


class HostSearchRequest(BaseModel):
    """Host search request."""

    query: str = Field(..., min_length=1, description="Search query")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    folder: Optional[str] = Field(None, description="Filter by folder")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    skip: int = Field(0, ge=0, description="Number of results to skip")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return")


class HostBulkActionRequest(BaseModel):
    """Request for bulk host operations."""

    host_ids: List[str] = Field(..., min_length=1, description="Host IDs for bulk operation")
    action: str = Field(..., description="Action to perform (delete/activate/deactivate/tag)")
    value: Optional[str] = Field(None, description="Value for the action (e.g., tag name)")


class HostBulkActionResponse(BaseModel):
    """Response from bulk host operation."""

    success: bool = Field(..., description="Overall success status")
    total_processed: int = Field(..., description="Number of hosts processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[dict] = Field(default_factory=list, description="Details of failed operations")

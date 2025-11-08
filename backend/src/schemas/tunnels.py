"""Pydantic schemas for tunnel operations."""

from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class TunnelType(str, Enum):
    """SSH tunnel type."""

    LOCAL = "local"      # Local port forwarding: localhost:local_port -> remote_host:remote_port
    REMOTE = "remote"    # Remote port forwarding: remote_host:remote_port -> localhost:local_port


class TunnelStatus(str, Enum):
    """Tunnel status states."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


class TunnelCreate(BaseModel):
    """Tunnel creation request."""

    host_id: str = Field(..., description="SSH host ID")
    name: str = Field(..., description="Tunnel name", min_length=1, max_length=255)
    tunnel_type: TunnelType = Field(..., description="Tunnel type: local or remote")
    local_port: int = Field(..., description="Local port number", ge=1, le=65535)
    remote_host: str = Field(..., description="Remote host or IP address")
    remote_port: int = Field(..., description="Remote port number", ge=1, le=65535)
    bind_address: Optional[str] = Field("127.0.0.1", description="Bind address for local forwarding")
    enabled: Optional[bool] = Field(True, description="Enable tunnel on creation")
    auto_reconnect: Optional[bool] = Field(True, description="Auto-reconnect on disconnect")


class TunnelUpdate(BaseModel):
    """Tunnel update request."""

    name: Optional[str] = Field(None, description="Tunnel name", min_length=1, max_length=255)
    local_port: Optional[int] = Field(None, description="Local port number", ge=1, le=65535)
    remote_host: Optional[str] = Field(None, description="Remote host or IP address")
    remote_port: Optional[int] = Field(None, description="Remote port number", ge=1, le=65535)
    bind_address: Optional[str] = Field(None, description="Bind address for local forwarding")
    enabled: Optional[bool] = Field(None, description="Enable/disable tunnel")
    auto_reconnect: Optional[bool] = Field(None, description="Auto-reconnect on disconnect")


class TunnelStatusInfo(BaseModel):
    """Tunnel status information."""

    status: TunnelStatus = Field(..., description="Current tunnel status")
    connected: bool = Field(..., description="Is tunnel currently connected")
    error: Optional[str] = Field(None, description="Error message if failed")
    last_error: Optional[str] = Field(None, description="Last error message")
    error_count: int = Field(0, description="Number of consecutive errors")
    last_connection_time: Optional[str] = Field(None, description="Last successful connection time")
    last_disconnection_time: Optional[str] = Field(None, description="Last disconnection time")
    uptime_seconds: int = Field(0, description="Current connection uptime in seconds")


class TunnelResponse(BaseModel):
    """Tunnel response model."""

    id: str = Field(..., description="Tunnel ID")
    host_id: str = Field(..., description="SSH host ID")
    name: str = Field(..., description="Tunnel name")
    tunnel_type: TunnelType = Field(..., description="Tunnel type")
    local_port: int = Field(..., description="Local port number")
    remote_host: str = Field(..., description="Remote host")
    remote_port: int = Field(..., description="Remote port number")
    bind_address: str = Field(..., description="Bind address")
    status: TunnelStatus = Field(..., description="Tunnel status")
    connected: bool = Field(..., description="Is connected")
    enabled: bool = Field(..., description="Is enabled")
    auto_reconnect: bool = Field(..., description="Auto-reconnect enabled")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    error: Optional[str] = Field(None, description="Current error message")


class TunnelListResponse(BaseModel):
    """List of tunnels response."""

    tunnels: list[TunnelResponse] = Field(..., description="List of tunnels")
    total: int = Field(..., description="Total tunnel count")
    status_summary: dict = Field(..., description="Status summary (connected, disconnected, failed counts)")


class TunnelStartRequest(BaseModel):
    """Request to start tunnel."""

    tunnel_id: str = Field(..., description="Tunnel ID to start")


class TunnelStopRequest(BaseModel):
    """Request to stop tunnel."""

    tunnel_id: str = Field(..., description="Tunnel ID to stop")


class TunnelReconnectRequest(BaseModel):
    """Request to reconnect tunnel."""

    tunnel_id: str = Field(..., description="Tunnel ID to reconnect")


class TunnelConnectionInfo(BaseModel):
    """Tunnel connection information."""

    status: TunnelStatus = Field(..., description="Connection status")
    connected: bool = Field(..., description="Is connected")
    local_address: Optional[str] = Field(None, description="Local bind address")
    local_port: int = Field(..., description="Local port")
    remote_address: Optional[str] = Field(None, description="Remote address")
    remote_port: int = Field(..., description="Remote port")
    error: Optional[str] = Field(None, description="Error message if failed")


class TunnelErrorResponse(BaseModel):
    """Tunnel error response."""

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    tunnel_id: Optional[str] = Field(None, description="Tunnel ID if applicable")

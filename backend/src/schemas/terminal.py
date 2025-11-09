"""Pydantic schemas for terminal API."""

from typing import Optional, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TerminalMessageType(str, Enum):
    """Terminal message types."""

    OUTPUT = "output"
    INPUT = "input"
    CONTROL = "control"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class TerminalSessionState(str, Enum):
    """Terminal session states."""

    CREATED = "created"
    CONNECTED = "connected"
    RUNNING = "running"
    DISCONNECTED = "disconnected"
    CLOSED = "closed"
    ERROR = "error"


class TerminalSessionCreate(BaseModel):
    """Create terminal session request."""

    rows: int = Field(24, ge=1, le=500, description="Terminal rows")
    cols: int = Field(80, ge=1, le=500, description="Terminal columns")
    env: Optional[dict] = Field(None, description="Environment variables")


class TerminalSessionResponse(BaseModel):
    """Terminal session response."""

    session_id: str = Field(..., description="Session ID")
    host_id: str = Field(..., description="Host ID")
    user_id: str = Field(..., description="User ID")
    state: TerminalSessionState = Field(..., description="Session state")
    rows: int = Field(..., description="Terminal rows")
    cols: int = Field(..., description="Terminal columns")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    connected: bool = Field(..., description="Is session connected")

    class Config:
        from_attributes = True


class TerminalSessionListResponse(BaseModel):
    """Terminal sessions list response."""

    items: List[TerminalSessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")


class TerminalMessage(BaseModel):
    """Terminal message."""

    type: TerminalMessageType = Field(..., description="Message type")
    session_id: str = Field(..., description="Session ID")
    data: str = Field(..., description="Message data")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")


class TerminalResizeRequest(BaseModel):
    """Terminal resize request."""

    rows: int = Field(..., ge=1, le=500, description="New terminal rows")
    cols: int = Field(..., ge=1, le=500, description="New terminal columns")


class TerminalInputRequest(BaseModel):
    """Terminal input request."""

    data: str = Field(..., description="Input data to send to terminal")


class TerminalExecuteRequest(BaseModel):
    """Terminal command execution request."""

    command: str = Field(..., description="Command to execute")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="Command timeout in seconds")


class TerminalOutputData(BaseModel):
    """Terminal output data."""

    data: str = Field(..., description="Output data")
    timestamp: datetime = Field(..., description="Output timestamp")
    size: int = Field(..., description="Data size in bytes")


class TerminalReconnectRequest(BaseModel):
    """Terminal reconnection request."""

    session_id: str = Field(..., description="Session ID to reconnect")


class TerminalTheme(str, Enum):
    """Terminal themes."""

    DRACULA = "dracula"
    SOLARIZED_DARK = "solarized-dark"
    SOLARIZED_LIGHT = "solarized-light"
    NORD = "nord"
    GRUVBOX = "gruvbox"
    ONE_DARK = "one-dark"
    MONOKAI = "monokai"


class TerminalPreferences(BaseModel):
    """Terminal preferences."""

    theme: TerminalTheme = Field(TerminalTheme.DRACULA, description="Terminal theme")
    font_size: int = Field(14, ge=8, le=32, description="Font size in pixels")
    font_family: str = Field("'Courier New', monospace", description="Font family")
    bell_enabled: bool = Field(True, description="Enable terminal bell")
    bell_type: str = Field("visual", description="Bell type: visual or audio")


class TerminalError(BaseModel):
    """Terminal error response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")

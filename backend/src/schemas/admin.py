"""Admin panel schemas for user and session management."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


# User Management Schemas

class UserListItem(BaseModel):
    """User item in admin list view."""
    id: str
    email: EmailStr
    username: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    role: str = "user"
    host_count: int = 0
    session_count: int = 0


class UserListResponse(BaseModel):
    """Response for user list endpoint."""
    total: int
    users: List[UserListItem]


# Session Management Schemas

class SessionInfo(BaseModel):
    """Session information for admin view."""
    session_id: str
    user_id: str
    user_email: EmailStr
    host_id: Optional[str] = None
    host_name: Optional[str] = None
    session_type: str  # "terminal", "stats", "files", etc.
    created_at: datetime
    last_activity: datetime
    status: str = "active"


class SessionListResponse(BaseModel):
    """Response for session list endpoint."""
    total: int
    active_sessions: int
    sessions: List[SessionInfo]


# OIDC Provider Schemas

class OIDCProviderConfig(BaseModel):
    """OIDC provider configuration."""
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    discovery_url: str = Field(..., min_length=1)
    scopes: List[str] = Field(default=["openid", "profile", "email"])
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OIDCProviderResponse(BaseModel):
    """Response model for OIDC provider (without sensitive data)."""
    id: str
    name: str
    display_name: str
    client_id: str
    discovery_url: str
    scopes: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OIDCProviderCreateRequest(BaseModel):
    """Request to create OIDC provider."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    discovery_url: str = Field(..., min_length=1)
    scopes: List[str] = Field(default=["openid", "profile", "email"])


class OIDCProviderUpdateRequest(BaseModel):
    """Request to update OIDC provider."""
    display_name: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    discovery_url: Optional[str] = None
    scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class OIDCProviderListResponse(BaseModel):
    """Response for OIDC provider list."""
    total: int
    providers: List[OIDCProviderResponse]


# Settings Schemas

class AdminSettingsResponse(BaseModel):
    """Admin settings response."""
    maintenance_mode: bool = False
    require_email_verification: bool = False
    allow_user_registration: bool = True
    session_timeout_minutes: int = 60
    max_concurrent_sessions_per_user: int = 10
    audit_log_retention_days: int = 90

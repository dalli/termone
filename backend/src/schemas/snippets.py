"""Pydantic schemas for snippet operations."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SnippetCreate(BaseModel):
    """Snippet creation request."""

    name: str = Field(..., description="Snippet name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Snippet description", max_length=1000)
    command: str = Field(..., description="Command to execute", min_length=1)
    tags: Optional[List[str]] = Field(None, description="Snippet tags for organization")
    public: Optional[bool] = Field(False, description="Make snippet public (shareable)")


class SnippetUpdate(BaseModel):
    """Snippet update request."""

    name: Optional[str] = Field(None, description="Snippet name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Snippet description", max_length=1000)
    command: Optional[str] = Field(None, description="Command to execute", min_length=1)
    tags: Optional[List[str]] = Field(None, description="Snippet tags")
    public: Optional[bool] = Field(None, description="Make snippet public")


class SnippetResponse(BaseModel):
    """Snippet response model."""

    id: str = Field(..., description="Snippet ID")
    user_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Snippet name")
    description: Optional[str] = Field(None, description="Snippet description")
    command: str = Field(..., description="Command")
    tags: Optional[List[str]] = Field(None, description="Tags")
    public: bool = Field(..., description="Is public")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    usage_count: int = Field(0, description="Number of times executed")


class SnippetExecuteRequest(BaseModel):
    """Snippet execution request."""

    session_id: Optional[str] = Field(None, description="Terminal session ID to execute in")
    target_host_id: Optional[str] = Field(None, description="Target host for execution")


class SnippetExecutionResult(BaseModel):
    """Result of snippet execution."""

    execution_id: str = Field(..., description="Execution ID")
    snippet_id: str = Field(..., description="Snippet ID")
    session_id: Optional[str] = Field(None, description="Session ID executed in")
    status: str = Field(..., description="Execution status (pending, running, completed, failed)")
    output: Optional[str] = Field(None, description="Command output")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: str = Field(..., description="Execution start time")
    completed_at: Optional[str] = Field(None, description="Execution completion time")


class SnippetBroadcastRequest(BaseModel):
    """Broadcast snippet to multiple sessions."""

    session_ids: List[str] = Field(..., description="List of session IDs to execute in")
    target_host_id: Optional[str] = Field(None, description="Target host")


class SnippetBroadcastResult(BaseModel):
    """Result of broadcast execution."""

    broadcast_id: str = Field(..., description="Broadcast ID")
    snippet_id: str = Field(..., description="Snippet ID")
    sessions: List[str] = Field(..., description="Session IDs")
    status: str = Field(..., description="Overall status")
    results: List[SnippetExecutionResult] = Field(..., description="Per-session results")


class SnippetListResponse(BaseModel):
    """List of snippets response."""

    snippets: List[SnippetResponse] = Field(..., description="List of snippets")
    total: int = Field(..., description="Total snippet count")
    tags: Optional[List[str]] = Field(None, description="Available tags")


class SnippetErrorResponse(BaseModel):
    """Snippet error response."""

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    snippet_id: Optional[str] = Field(None, description="Snippet ID if applicable")

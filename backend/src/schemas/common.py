"""Common response schemas used across the API."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail model."""

    field: Optional[str] = Field(None, description="Field name if applicable")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = Field(False, description="Success indicator")
    error: ErrorDetail = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response model."""

    success: bool = Field(True, description="Success indicator")
    data: Optional[T] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Success message")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    success: bool = Field(True, description="Success indicator")
    data: list[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination information")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field("0.1.0", description="API version")
    database: str = Field(..., description="Database status")

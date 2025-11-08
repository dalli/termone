"""Error handling middleware."""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json

from src.exceptions import TermoneException


async def error_handler(request: Request, exc: Exception) -> Response:
    """Handle exceptions and return standard error response."""
    if isinstance(exc, TermoneException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": exc.message,
                    "code": exc.code,
                    "field": getattr(exc, "field", None),
                },
                "request_id": request.headers.get("X-Request-ID"),
            },
        )
    
    # Generic error
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
            },
        },
    )

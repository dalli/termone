"""Authentication middleware."""

from fastapi import Request
from src.services.jwt_service import get_jwt_service
from src.exceptions import AuthenticationException


async def verify_token(request: Request):
    """Verify JWT token from request header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationException("Missing or invalid authorization header")

    token = auth_header[7:]
    jwt_service = get_jwt_service()
    payload = jwt_service.verify_token(token)
    request.state.user_id = payload.get("sub")
    request.state.user_claims = payload

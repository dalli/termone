"""API dependencies for FastAPI routes."""

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db as _get_db
from src.models.user import User
from src.services.jwt_service import get_jwt_service
from src.exceptions import AuthenticationException


async def get_db() -> AsyncSession:
    """Get database session."""
    async for session in _get_db():
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None, alias="Authorization"),
) -> User:
    """Get current authenticated user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationException("Missing or invalid authorization header")
    
    token = authorization[7:]
    jwt_service = get_jwt_service()
    
    try:
        payload = jwt_service.verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationException("Invalid token: missing user ID")
        
        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationException("User not found")
        
        if not user.is_active:
            raise AuthenticationException("User account is inactive")
        
        return user
    except Exception as e:
        if isinstance(e, AuthenticationException):
            raise
        raise AuthenticationException(f"Authentication failed: {str(e)}")


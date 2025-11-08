"""JWT token management service."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt

from src.config import get_settings
from src.exceptions import AuthenticationException

settings = get_settings()


class JWTService:
    """Service for JWT token generation and validation."""

    def __init__(self):
        """Initialize JWT service."""
        self.secret = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS

    def create_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create JWT token.

        Args:
            data: Claims to include in token
            expires_delta: Custom expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token claims

        Raises:
            AuthenticationException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise AuthenticationException(f"Invalid token: {str(e)}")

    def refresh_token(self, token: str) -> str:
        """
        Generate a new token from an existing one.

        Args:
            token: JWT token to refresh

        Returns:
            New JWT token

        Raises:
            AuthenticationException: If token is invalid
        """
        payload = self.verify_token(token)
        # Remove exp to let create_token set it
        payload.pop("exp", None)
        return self.create_token(payload)


# Global instance
_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """Get or create JWT service instance."""
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
    return _jwt_service

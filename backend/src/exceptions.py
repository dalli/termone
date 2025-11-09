"""Custom exception classes for the application."""


class TermoneException(Exception):
    """Base exception for all Termone errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationException(TermoneException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)


class AuthorizationException(TermoneException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "UNAUTHORIZED", 403)


class PermissionException(AuthorizationException):
    """Alias for AuthorizationException for backward compatibility."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)


class ValidationException(TermoneException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", field: str | None = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR", 422)


class ResourceNotFoundException(TermoneException):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, "NOT_FOUND", 404)


class NotFoundException(ResourceNotFoundException):
    """Alias for ResourceNotFoundException for backward compatibility."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(resource, identifier)


class ConflictException(TermoneException):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, "CONFLICT", 409)


class RateLimitException(TermoneException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMITED", 429)


class DatabaseException(TermoneException):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database error"):
        super().__init__(message, "DATABASE_ERROR", 500)


class SSHException(TermoneException):
    """Raised when SSH operation fails."""

    def __init__(self, message: str = "SSH connection failed"):
        super().__init__(message, "SSH_ERROR", 500)


class EncryptionException(TermoneException):
    """Raised when encryption/decryption fails."""

    def __init__(self, message: str = "Encryption failed"):
        super().__init__(message, "ENCRYPTION_ERROR", 500)


class OIDCException(TermoneException):
    """Raised when OIDC operation fails."""

    def __init__(self, message: str = "OIDC error"):
        super().__init__(message, "OIDC_ERROR", 500)

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration management."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://termone_user:termone_password@localhost/termone_db"

    # Security
    ENCRYPTION_MASTER_KEY: str = "test-key-32-bytes-minimum-12345"  # Change in production
    JWT_SECRET: str = "test-secret-minimum-32-characters"  # Change in production
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 1
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30
    TOTP_ISSUER: str = "Termone"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 4
    DEBUG: bool = False
    TESTING: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate Limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300
    RATE_LIMIT_API_CALLS_PER_MINUTE: int = 100

    # SSH Configuration
    SSH_CONNECTION_TIMEOUT_SECONDS: int = 30
    SSH_COMMAND_TIMEOUT_SECONDS: int = 300
    SSH_MAX_CONCURRENT_SESSIONS: int = 50
    SSH_KEY_PATH: str = "/home/termone/.ssh/id_rsa"
    SSH_KNOWN_HOSTS_PATH: str = "/home/termone/.ssh/known_hosts"

    # Terminal Session
    TERMINAL_SESSION_TIMEOUT_MINUTES: int = 30
    TERMINAL_IDLE_TIMEOUT_MINUTES: int = 5
    TERMINAL_HEARTBEAT_INTERVAL_SECONDS: int = 30

    # File Transfer
    FILE_UPLOAD_MAX_SIZE_MB: int = 100
    FILE_DOWNLOAD_CHUNK_SIZE_KB: int = 256
    SFTP_TIMEOUT_SECONDS: int = 30

    # WebSocket
    WEBSOCKET_PING_INTERVAL_SECONDS: int = 30
    WEBSOCKET_RECONNECT_TIMEOUT_SECONDS: int = 30
    WEBSOCKET_BUFFER_SIZE_MB: int = 10

    # OIDC
    OIDC_DISCOVERY_URL: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_CLIENT_SECRET: str | None = None
    OIDC_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    OIDC_SCOPES: str = "openid,profile,email"

    # Audit Logging
    AUDIT_LOG_RETENTION_DAYS: int = 90
    AUDIT_LOG_LEVEL: str = "INFO"

    # Redis (optional)
    REDIS_URL: str | None = None

    # Email (optional)
    SMTP_SERVER: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_ADDRESS: str | None = None

    # Logging
    LOG_FORMAT: str = "json"
    LOG_OUTPUT: str = "stdout"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

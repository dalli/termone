import uuid
from typing import List

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class SSHHost(Base, TimestampMixin):
    """SSH Host model for managing remote servers."""

    __tablename__ = "ssh_host"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Comma-separated
    folder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    credentials: Mapped[List["Credential"]] = relationship(
        "Credential",
        back_populates="host",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    ssh_sessions: Mapped[List["SSHSession"]] = relationship(
        "SSHSession", back_populates="host", cascade="all, delete-orphan"
    )
    terminal_sessions: Mapped[List["TerminalSession"]] = relationship(
        "TerminalSession", back_populates="host", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        foreign_keys="AuditLog.host_id",
        back_populates="host",
        cascade="all, delete-orphan",
    )
    tunnels: Mapped[List["SSHTunnel"]] = relationship(
        "SSHTunnel", back_populates="host", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SSHHost {self.name}>"


class Credential(Base, TimestampMixin):
    """Credential model for storing SSH authentication credentials."""

    __tablename__ = "credential"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    host_id: Mapped[str] = mapped_column(String(36), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "password" or "key"
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)  # AES-256-GCM encrypted
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    passphrase_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)  # For key passphrase

    # Relationships
    host: Mapped["SSHHost"] = relationship("SSHHost", back_populates="credentials")

    def __repr__(self) -> str:
        return f"<Credential {self.id} for {self.host_id}>"


class OIDCProvider(Base, TimestampMixin):
    """OIDC Provider configuration for SSO."""

    __tablename__ = "oidc_provider"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    discovery_url: Mapped[str] = mapped_column(String(500), nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    client_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    scopes: Mapped[str] = mapped_column(String(500), default="openid,profile,email", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<OIDCProvider {self.name}>"

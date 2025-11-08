import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


# Association tables for many-to-many relationships
user_role_association = Table(
    "user_role",
    Base.metadata,
    Column("user_id", String, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)

role_permission_association = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", String, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        String,
        ForeignKey("permission.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_role_association,
        back_populates="users",
        lazy="selectin",
    )
    totp_secret: Mapped["TOTPSecret | None"] = relationship(
        "TOTPSecret", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Role(Base, TimestampMixin):
    """Role model for RBAC."""

    __tablename__ = "role"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_role_association,
        back_populates="roles",
        lazy="selectin",
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permission_association,
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Permission(Base, TimestampMixin):
    """Permission model for RBAC."""

    __tablename__ = "permission"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    resource: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "host", "file"
    action: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "create", "read"

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permission_association,
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class TOTPSecret(Base, TimestampMixin):
    """TOTP (Time-based One-Time Password) secret for 2FA."""

    __tablename__ = "totp_secret"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backup_codes: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="totp_secret")

    def __repr__(self) -> str:
        return f"<TOTPSecret {self.user_id}>"


class RefreshToken(Base, TimestampMixin):
    """Refresh token for JWT authentication."""

    __tablename__ = "refresh_token"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken {self.user_id}>"

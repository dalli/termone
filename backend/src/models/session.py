import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class SSHSession(Base, TimestampMixin):
    """SSH Session model for managing SSH connections."""

    __tablename__ = "ssh_session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    host_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ssh_host.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    session_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    host: Mapped["SSHHost"] = relationship("SSHHost", back_populates="ssh_sessions")

    def __repr__(self) -> str:
        return f"<SSHSession {self.id} for {self.host_id}>"


class TerminalSession(Base, TimestampMixin):
    """Terminal Session model for interactive shell access."""

    __tablename__ = "terminal_session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    host_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ssh_host.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    session_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    pty_rows: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    pty_cols: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    terminal_type: Mapped[str] = mapped_column(String(50), default="xterm-256color", nullable=False)
    shell: Mapped[str] = mapped_column(String(255), default="/bin/bash", nullable=False)

    # Relationships
    host: Mapped["SSHHost"] = relationship("SSHHost", back_populates="terminal_sessions")

    def __repr__(self) -> str:
        return f"<TerminalSession {self.id} for {self.host_id}>"

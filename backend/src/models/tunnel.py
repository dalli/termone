import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class SSHTunnel(Base, TimestampMixin):
    """SSH Tunnel model for managing port forwarding."""

    __tablename__ = "ssh_tunnel"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    host_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ssh_host.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tunnel_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "local" or "remote"
    local_bind_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    local_bind_port: Mapped[int] = mapped_column(Integer, nullable=False)
    remote_bind_host: Mapped[str] = mapped_column(String(255), nullable=False)
    remote_bind_port: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_connection_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    host: Mapped["SSHHost"] = relationship("SSHHost", back_populates="tunnels")

    def __repr__(self) -> str:
        return f"<SSHTunnel {self.name}>"

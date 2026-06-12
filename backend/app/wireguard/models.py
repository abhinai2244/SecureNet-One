"""
SecureNet One - WireGuard Peer Model
SQLAlchemy model for WireGuard peer configurations.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDMixin, TimestampMixin


class WireGuardPeer(Base, UUIDMixin, TimestampMixin):
    """WireGuard peer configuration."""

    __tablename__ = "wireguard_peers"

    device_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    public_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    private_key_encrypted: Mapped[str] = mapped_column(String(512), nullable=True)
    preshared_key_encrypted: Mapped[str] = mapped_column(String(512), nullable=True)
    allowed_ips: Mapped[str] = mapped_column(String(255), nullable=False, default="0.0.0.0/0")
    endpoint: Mapped[str] = mapped_column(String(255), nullable=True)
    persistent_keepalive: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    last_handshake: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    tx_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    rx_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Relationships
    device = relationship("Device", lazy="selectin")

    def __repr__(self) -> str:
        return f"<WireGuardPeer device={self.device_id}>"

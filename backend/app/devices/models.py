"""
SecureNet One - Device Model
SQLAlchemy model for the devices table.
"""

import enum

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy import DateTime

from app.core.database import Base, UUIDMixin, TimestampMixin


class DeviceStatus(str, enum.Enum):
    """Device connection status."""
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"


class Device(Base, UUIDMixin, TimestampMixin):
    """Device database model."""

    __tablename__ = "devices"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    os: Mapped[str] = mapped_column(String(100), nullable=False)
    os_version: Mapped[str] = mapped_column(String(100), nullable=True)
    agent_version: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(
        SQLEnum(DeviceStatus, name="device_status"),
        default=DeviceStatus.OFFLINE,
        nullable=False,
    )
    public_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    assigned_ip: Mapped[str] = mapped_column(String(45), unique=True, nullable=True)
    last_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Posture data
    disk_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    antivirus_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    cpu_info: Mapped[str] = mapped_column(String(255), nullable=True)
    ram_bytes: Mapped[int] = mapped_column(BigInteger, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=True)

    # Relationships
    user = relationship("User", back_populates="devices", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Device {self.hostname} ({self.status.value})>"

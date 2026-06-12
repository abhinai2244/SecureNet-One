"""
SecureNet One - Log Models
SQLAlchemy models for device logs, DNS logs, and audit logs.
"""

import enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.core.database import Base, UUIDMixin


class DeviceEventType(str, enum.Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    POSTURE = "posture"
    KEY_ROTATION = "key_rotation"


class DnsAction(str, enum.Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REDIRECT = "redirect"


class DeviceLog(Base, UUIDMixin):
    """Device event log."""

    __tablename__ = "device_logs"

    device_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[DeviceEventType] = mapped_column(
        SQLEnum(DeviceEventType, name="device_event_type"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class DnsLog(Base, UUIDMixin):
    """DNS query log."""

    __tablename__ = "dns_logs"

    device_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True
    )
    query_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    query_type: Mapped[str] = mapped_column(String(10), nullable=False)
    response_code: Mapped[str] = mapped_column(String(20), nullable=True)
    action: Mapped[DnsAction] = mapped_column(
        SQLEnum(DnsAction, name="dns_action"), nullable=False
    )
    policy_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True
    )
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class AuditLog(Base, UUIDMixin):
    """Admin action audit log."""

    __tablename__ = "audit_logs"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=True)
    changes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

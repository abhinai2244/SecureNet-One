"""
SecureNet One - Policy Model
SQLAlchemy model for the policies table.
"""

import enum

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDMixin, TimestampMixin


class PolicyType(str, enum.Enum):
    """Policy type enumeration."""
    DNS = "dns"
    TUNNEL = "tunnel"
    ACCESS = "access"
    POSTURE = "posture"


class Policy(Base, UUIDMixin, TimestampMixin):
    """Policy database model."""

    __tablename__ = "policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[PolicyType] = mapped_column(
        SQLEnum(PolicyType, name="policy_type"), nullable=False
    )
    rules: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Policy {self.name} ({self.type.value})>"

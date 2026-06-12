"""
SecureNet One - Device Schemas
Pydantic models for device request/response validation.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────
class DeviceRegisterRequest(BaseModel):
    """Schema for device registration."""
    device_name: str = Field(..., min_length=1, max_length=255)
    hostname: str = Field(..., min_length=1, max_length=255)
    os: str = Field(..., min_length=1, max_length=100)
    os_version: Optional[str] = None
    agent_version: Optional[str] = None
    public_key: Optional[str] = None


class DeviceHeartbeatRequest(BaseModel):
    """Schema for device heartbeat with posture data."""
    device_id: UUID
    os: Optional[str] = None
    os_version: Optional[str] = None
    agent_version: Optional[str] = None
    disk_encrypted: Optional[bool] = None
    antivirus_active: Optional[bool] = None
    cpu_info: Optional[str] = None
    ram_bytes: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None


class DeviceUpdateRequest(BaseModel):
    """Schema for updating device information."""
    device_name: Optional[str] = None
    hostname: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None


# ── Response Schemas ─────────────────────────────────────────────
class DeviceResponse(BaseModel):
    """Device information response."""
    id: UUID
    user_id: UUID
    device_name: str
    hostname: str
    os: str
    os_version: Optional[str] = None
    agent_version: Optional[str] = None
    status: str
    public_key: Optional[str] = None
    assigned_ip: Optional[str] = None
    last_ip: Optional[str] = None
    last_seen: Optional[datetime] = None
    disk_encrypted: Optional[bool] = None
    antivirus_active: Optional[bool] = None
    cpu_info: Optional[str] = None
    ram_bytes: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    """Paginated list of devices."""
    devices: list[DeviceResponse]
    total: int
    page: int
    page_size: int


class DeviceStatsResponse(BaseModel):
    """Dashboard statistics for devices."""
    total_devices: int
    online_devices: int
    offline_devices: int
    warning_devices: int
    encrypted_devices: int
    antivirus_active_devices: int


class HeartbeatResponse(BaseModel):
    """Heartbeat acknowledgment response."""
    status: str = "ok"
    server_time: datetime
    next_heartbeat_seconds: int

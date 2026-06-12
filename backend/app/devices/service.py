"""
SecureNet One - Device Service
Business logic for device management.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import set_device_online
from app.devices.models import DeviceStatus
from app.devices.repository import DeviceRepository
from app.devices.schemas import (
    DeviceHeartbeatRequest,
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceStatsResponse,
    HeartbeatResponse,
)
from app.shared.exceptions import AlreadyExistsException, ForbiddenException, NotFoundException

settings = get_settings()


class DeviceService:
    """Service for device business logic."""

    def __init__(self, db: AsyncSession):
        self.repo = DeviceRepository(db)

    async def register_device(
        self, user_id: str, data: DeviceRegisterRequest
    ) -> DeviceResponse:
        """Register a new device for a user."""
        # Check for duplicate public key
        if data.public_key:
            existing = await self.repo.get_by_public_key(data.public_key)
            if existing:
                raise AlreadyExistsException("Device", "public_key")

        # Allocate IP address
        assigned_ip = await self.repo.get_next_ip()

        device = await self.repo.create(
            user_id=UUID(user_id),
            device_name=data.device_name,
            hostname=data.hostname,
            os=data.os,
            os_version=data.os_version,
            agent_version=data.agent_version,
            public_key=data.public_key,
            assigned_ip=assigned_ip,
            status=DeviceStatus.OFFLINE,
        )

        return DeviceResponse.model_validate(device)

    async def heartbeat(
        self, data: DeviceHeartbeatRequest, source_ip: str = None
    ) -> HeartbeatResponse:
        """Process device heartbeat with posture data."""
        device = await self.repo.get_by_id(data.device_id)
        if not device:
            raise NotFoundException("Device", str(data.device_id))

        # Update device posture data
        posture_data = {}
        if data.os:
            posture_data["os"] = data.os
        if data.os_version:
            posture_data["os_version"] = data.os_version
        if data.agent_version:
            posture_data["agent_version"] = data.agent_version
        if data.disk_encrypted is not None:
            posture_data["disk_encrypted"] = data.disk_encrypted
        if data.antivirus_active is not None:
            posture_data["antivirus_active"] = data.antivirus_active
        if data.cpu_info:
            posture_data["cpu_info"] = data.cpu_info
        if data.ram_bytes is not None:
            posture_data["ram_bytes"] = data.ram_bytes
        if source_ip:
            posture_data["last_ip"] = source_ip
        if data.metadata:
            posture_data["metadata_json"] = data.metadata

        await self.repo.update_heartbeat(device, **posture_data)

        # Update Redis cache for online status
        await set_device_online(
            str(device.id),
            ttl=settings.DEVICE_OFFLINE_THRESHOLD_SECONDS,
        )

        return HeartbeatResponse(
            server_time=datetime.now(timezone.utc),
            next_heartbeat_seconds=settings.HEARTBEAT_INTERVAL_SECONDS,
        )

    async def get_device(self, device_id: str, user_id: str = None) -> DeviceResponse:
        """Get a single device by ID."""
        device = await self.repo.get_by_id(UUID(device_id))
        if not device:
            raise NotFoundException("Device", device_id)
        return DeviceResponse.model_validate(device)

    async def list_devices(
        self, offset: int = 0, limit: int = 20, status_filter: str = None
    ) -> tuple[list[DeviceResponse], int]:
        """List all devices with pagination."""
        status_enum = DeviceStatus(status_filter) if status_filter else None
        devices, total = await self.repo.get_all(offset, limit, status_enum)
        return [DeviceResponse.model_validate(d) for d in devices], total

    async def get_user_devices(self, user_id: str) -> list[DeviceResponse]:
        """Get all devices belonging to a user."""
        devices = await self.repo.get_by_user(UUID(user_id))
        return [DeviceResponse.model_validate(d) for d in devices]

    async def get_stats(self) -> DeviceStatsResponse:
        """Get device dashboard statistics."""
        stats = await self.repo.get_stats()
        return DeviceStatsResponse(**stats)

    async def delete_device(self, device_id: str, user_id: str, role: str) -> None:
        """Delete a device."""
        device = await self.repo.get_by_id(UUID(device_id))
        if not device:
            raise NotFoundException("Device", device_id)

        # Only admins or device owner can delete
        if role not in ("super_admin", "admin") and str(device.user_id) != user_id:
            raise ForbiddenException("Cannot delete another user's device")

        await self.repo.delete(device)

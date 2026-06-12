"""
SecureNet One - Device Repository
Database access layer for device operations.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.devices.models import Device, DeviceStatus


class DeviceRepository:
    """Repository for device database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, device_id: UUID) -> Optional[Device]:
        """Get device by ID."""
        result = await self.db.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[Device]:
        """Get all devices for a user."""
        result = await self.db.execute(
            select(Device).where(Device.user_id == user_id).order_by(Device.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_public_key(self, public_key: str) -> Optional[Device]:
        """Get device by WireGuard public key."""
        result = await self.db.execute(
            select(Device).where(Device.public_key == public_key)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, **kwargs) -> Device:
        """Create a new device."""
        device = Device(user_id=user_id, **kwargs)
        self.db.add(device)
        await self.db.flush()
        await self.db.refresh(device)
        return device

    async def update(self, device: Device, **kwargs) -> Device:
        """Update device fields."""
        for key, value in kwargs.items():
            if hasattr(device, key) and value is not None:
                setattr(device, key, value)
        await self.db.flush()
        await self.db.refresh(device)
        return device

    async def update_heartbeat(self, device: Device, **posture_data) -> Device:
        """Update device with heartbeat and posture data."""
        device.last_seen = datetime.now(timezone.utc)
        device.status = DeviceStatus.ONLINE
        for key, value in posture_data.items():
            if hasattr(device, key) and value is not None:
                setattr(device, key, value)
        await self.db.flush()
        await self.db.refresh(device)
        return device

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        status_filter: Optional[DeviceStatus] = None,
    ) -> tuple[list[Device], int]:
        """Get all devices with pagination and optional filtering."""
        query = select(Device)
        count_query = select(func.count(Device.id))

        if status_filter:
            query = query.where(Device.status == status_filter)
            count_query = count_query.where(Device.status == status_filter)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Device.last_seen.desc().nullslast()).offset(offset).limit(limit)
        )
        devices = list(result.scalars().all())

        return devices, total

    async def get_stats(self) -> dict:
        """Get device statistics."""
        total = await self.db.execute(select(func.count(Device.id)))
        online = await self.db.execute(
            select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
        )
        offline = await self.db.execute(
            select(func.count(Device.id)).where(Device.status == DeviceStatus.OFFLINE)
        )
        warning = await self.db.execute(
            select(func.count(Device.id)).where(Device.status == DeviceStatus.WARNING)
        )
        encrypted = await self.db.execute(
            select(func.count(Device.id)).where(Device.disk_encrypted == True)
        )
        av_active = await self.db.execute(
            select(func.count(Device.id)).where(Device.antivirus_active == True)
        )
        return {
            "total_devices": total.scalar_one(),
            "online_devices": online.scalar_one(),
            "offline_devices": offline.scalar_one(),
            "warning_devices": warning.scalar_one(),
            "encrypted_devices": encrypted.scalar_one(),
            "antivirus_active_devices": av_active.scalar_one(),
        }

    async def delete(self, device: Device):
        """Delete a device."""
        await self.db.delete(device)
        await self.db.flush()

    async def get_next_ip(self, subnet: str = "10.0.0") -> str:
        """Allocate the next available IP in the subnet."""
        result = await self.db.execute(
            select(Device.assigned_ip)
            .where(Device.assigned_ip.isnot(None))
            .order_by(Device.assigned_ip.desc())
        )
        existing_ips = [row[0] for row in result.all()]

        if not existing_ips:
            return f"{subnet}.2"  # .1 is reserved for gateway

        # Find the highest IP and increment
        last_octet = max(int(ip.split(".")[-1]) for ip in existing_ips)
        return f"{subnet}.{last_octet + 1}"

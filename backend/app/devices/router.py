"""
SecureNet One - Device Router
API endpoints for device management and monitoring.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.core.security import require_admin
from app.devices.schemas import (
    DeviceHeartbeatRequest,
    DeviceListResponse,
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceStatsResponse,
    HeartbeatResponse,
)
from app.devices.service import DeviceService
from app.shared.dependencies import CurrentUserId, CurrentUserRole, DbSession, Pagination

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/register", response_model=DeviceResponse, status_code=201)
async def register_device(
    data: DeviceRegisterRequest,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Register a new device for the authenticated user."""
    service = DeviceService(db)
    return await service.register_device(user_id, data)


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def device_heartbeat(
    data: DeviceHeartbeatRequest,
    request: Request,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Receive device heartbeat with posture data."""
    source_ip = request.client.host if request.client else None
    service = DeviceService(db)
    return await service.heartbeat(data, source_ip)


@router.get("/stats", response_model=DeviceStatsResponse)
async def get_device_stats(
    db: DbSession,
    _admin_id: str = Depends(require_admin),
):
    """Get device dashboard statistics (admin only)."""
    service = DeviceService(db)
    return await service.get_stats()


@router.get("/my-devices", response_model=list[DeviceResponse])
async def get_my_devices(user_id: CurrentUserId, db: DbSession):
    """Get all devices belonging to the authenticated user."""
    service = DeviceService(db)
    return await service.get_user_devices(user_id)


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    db: DbSession,
    pagination: Pagination,
    status: Optional[str] = Query(None, regex="^(online|offline|warning)$"),
    _admin_id: str = Depends(require_admin),
):
    """List all devices with pagination (admin only)."""
    service = DeviceService(db)
    devices, total = await service.list_devices(
        pagination.offset, pagination.limit, status
    )
    return DeviceListResponse(
        devices=devices,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Get a single device by ID."""
    service = DeviceService(db)
    return await service.get_device(device_id, user_id)


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: str,
    user_id: CurrentUserId,
    role: CurrentUserRole,
    db: DbSession,
):
    """Delete a device."""
    service = DeviceService(db)
    await service.delete_device(device_id, user_id, role)

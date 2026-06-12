"""
SecureNet One - WireGuard Router
API endpoints for WireGuard configuration management.
"""

from fastapi import APIRouter, Depends

from app.core.security import require_admin
from app.shared.dependencies import CurrentUserId, DbSession
from app.wireguard.schemas import (
    KeyRotationResponse,
    WireGuardConfigResponse,
    WireGuardStatusResponse,
)
from app.wireguard.service import WireGuardService

router = APIRouter(prefix="/wireguard", tags=["WireGuard"])


@router.get("/config/{device_id}", response_model=WireGuardConfigResponse)
async def get_wireguard_config(
    device_id: str,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Get WireGuard configuration for a device."""
    service = WireGuardService(db)
    return await service.get_config(device_id)


@router.post("/rotate-keys/{device_id}", response_model=KeyRotationResponse)
async def rotate_keys(
    device_id: str,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Rotate WireGuard keys for a device."""
    service = WireGuardService(db)
    return await service.rotate_keys(device_id)


@router.get("/status", response_model=WireGuardStatusResponse)
async def get_wireguard_status(
    db: DbSession,
    _admin_id: str = Depends(require_admin),
):
    """Get overall WireGuard tunnel status (admin only)."""
    service = WireGuardService(db)
    return await service.get_status()

"""
SecureNet One - Log Router
API endpoints for viewing logs.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.core.security import require_admin, require_analyst, require_super_admin
from app.logs.schemas import (
    AuditLogListResponse,
    DeviceLogCreateRequest,
    DeviceLogListResponse,
    DeviceLogResponse,
    DnsLogListResponse,
    LogStatsResponse,
)
from app.logs.service import LogService
from app.shared.dependencies import CurrentUserId, DbSession, Pagination

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats(
    db: DbSession,
    _admin_id: str = Depends(require_analyst),
):
    """Get log statistics for dashboard (analyst+ only)."""
    service = LogService(db)
    return await service.get_log_stats()


@router.post("/report", response_model=DeviceLogResponse, status_code=201)
async def report_device_log(
    data: DeviceLogCreateRequest,
    request: Request,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Agent reports a device event log."""
    source_ip = request.client.host if request.client else None
    service = LogService(db)
    return await service.create_device_log(data, source_ip)


@router.get("/devices", response_model=DeviceLogListResponse)
async def get_device_logs(
    db: DbSession,
    pagination: Pagination,
    device_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    _admin_id: str = Depends(require_analyst),
):
    """Get device connection/event logs (analyst+ only)."""
    service = LogService(db)
    logs, total = await service.get_device_logs(
        pagination.offset, pagination.limit, device_id, event_type
    )
    return DeviceLogListResponse(
        logs=logs, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/dns", response_model=DnsLogListResponse)
async def get_dns_logs(
    db: DbSession,
    pagination: Pagination,
    device_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None, regex="^(allow|block|redirect)$"),
    _admin_id: str = Depends(require_analyst),
):
    """Get DNS query logs (analyst+ only)."""
    service = LogService(db)
    logs, total = await service.get_dns_logs(
        pagination.offset, pagination.limit, device_id, action
    )
    return DnsLogListResponse(
        logs=logs, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/audit", response_model=AuditLogListResponse)
async def get_audit_logs(
    db: DbSession,
    pagination: Pagination,
    _admin_id: str = Depends(require_super_admin),
):
    """Get admin audit trail (super admin only)."""
    service = LogService(db)
    logs, total = await service.get_audit_logs(pagination.offset, pagination.limit)
    return AuditLogListResponse(
        logs=logs, total=total, page=pagination.page, page_size=pagination.page_size
    )

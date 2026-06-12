"""
SecureNet One - Log Service
Business logic for log management.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.logs.models import DeviceEventType
from app.logs.repository import LogRepository
from app.logs.schemas import (
    AuditLogResponse,
    DeviceLogCreateRequest,
    DeviceLogResponse,
    DnsLogResponse,
    LogStatsResponse,
)


class LogService:
    """Service for log business logic."""

    def __init__(self, db: AsyncSession):
        self.repo = LogRepository(db)

    async def create_device_log(
        self, data: DeviceLogCreateRequest, source_ip: str = None
    ) -> DeviceLogResponse:
        log = await self.repo.create_device_log(
            device_id=data.device_id,
            event_type=DeviceEventType(data.event_type),
            payload=data.payload,
            source_ip=source_ip,
        )
        return DeviceLogResponse.model_validate(log)

    async def get_device_logs(
        self, offset: int = 0, limit: int = 50, device_id: str = None, event_type: str = None
    ) -> tuple[list[DeviceLogResponse], int]:
        device_uuid = UUID(device_id) if device_id else None
        logs, total = await self.repo.get_device_logs(offset, limit, device_uuid, event_type)
        return [DeviceLogResponse.model_validate(l) for l in logs], total

    async def get_dns_logs(
        self, offset: int = 0, limit: int = 50, device_id: str = None, action: str = None
    ) -> tuple[list[DnsLogResponse], int]:
        device_uuid = UUID(device_id) if device_id else None
        logs, total = await self.repo.get_dns_logs(offset, limit, device_uuid, action)
        return [DnsLogResponse.model_validate(l) for l in logs], total

    async def get_audit_logs(
        self, offset: int = 0, limit: int = 50
    ) -> tuple[list[AuditLogResponse], int]:
        logs, total = await self.repo.get_audit_logs(offset, limit)
        return [AuditLogResponse.model_validate(l) for l in logs], total

    async def get_log_stats(self) -> LogStatsResponse:
        total_dns = await self.repo.get_dns_query_count()
        blocked = await self.repo.get_blocked_query_count()
        connections = await self.repo.get_connection_count()
        errors = await self.repo.get_error_count()
        top_blocked = await self.repo.get_top_blocked_domains()
        top_requested = await self.repo.get_top_requested_domains()
        avg_latency = await self.repo.get_average_latency()
        recent = await self.repo.get_recent_events()

        return LogStatsResponse(
            total_dns_queries=total_dns,
            blocked_queries=blocked,
            total_connections=connections,
            total_errors=errors,
            top_blocked_domains=top_blocked,
            top_requested_domains=top_requested,
            average_latency_ms=avg_latency,
            recent_events=[DeviceLogResponse.model_validate(e) for e in recent],
        )

"""
SecureNet One - Log Repository
Database access layer for log operations.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logs.models import AuditLog, DeviceEventType, DeviceLog, DnsAction, DnsLog


class LogRepository:
    """Repository for log database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Device Logs ──────────────────────────────────────────────
    async def create_device_log(
        self,
        device_id: UUID,
        event_type: DeviceEventType,
        payload: dict = None,
        source_ip: str = None,
    ) -> DeviceLog:
        log = DeviceLog(
            device_id=device_id,
            event_type=event_type,
            payload=payload or {},
            source_ip=source_ip,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_device_logs(
        self,
        offset: int = 0,
        limit: int = 50,
        device_id: Optional[UUID] = None,
        event_type: Optional[str] = None,
    ) -> tuple[list[DeviceLog], int]:
        query = select(DeviceLog)
        count_query = select(func.count(DeviceLog.id))

        if device_id:
            query = query.where(DeviceLog.device_id == device_id)
            count_query = count_query.where(DeviceLog.device_id == device_id)
        if event_type:
            query = query.where(DeviceLog.event_type == DeviceEventType(event_type))
            count_query = count_query.where(DeviceLog.event_type == DeviceEventType(event_type))

        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(desc(DeviceLog.timestamp)).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    # ── DNS Logs ─────────────────────────────────────────────────
    async def create_dns_log(self, **kwargs) -> DnsLog:
        log = DnsLog(timestamp=datetime.now(timezone.utc), **kwargs)
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_dns_logs(
        self,
        offset: int = 0,
        limit: int = 50,
        device_id: Optional[UUID] = None,
        action: Optional[str] = None,
    ) -> tuple[list[DnsLog], int]:
        query = select(DnsLog)
        count_query = select(func.count(DnsLog.id))

        if device_id:
            query = query.where(DnsLog.device_id == device_id)
            count_query = count_query.where(DnsLog.device_id == device_id)
        if action:
            query = query.where(DnsLog.action == DnsAction(action))
            count_query = count_query.where(DnsLog.action == DnsAction(action))

        total = (await self.db.execute(count_query)).scalar_one()
        result = await self.db.execute(
            query.order_by(desc(DnsLog.timestamp)).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_top_blocked_domains(self, limit: int = 10) -> list[dict]:
        result = await self.db.execute(
            select(DnsLog.query_name, func.count(DnsLog.id).label("count"))
            .where(DnsLog.action == DnsAction.BLOCK)
            .group_by(DnsLog.query_name)
            .order_by(desc("count"))
            .limit(limit)
        )
        return [{"domain": row[0], "count": row[1]} for row in result.all()]

    async def get_top_requested_domains(self, limit: int = 10) -> list[dict]:
        result = await self.db.execute(
            select(DnsLog.query_name, func.count(DnsLog.id).label("count"))
            .group_by(DnsLog.query_name)
            .order_by(desc("count"))
            .limit(limit)
        )
        return [{"domain": row[0], "count": row[1]} for row in result.all()]

    async def get_average_latency(self) -> int:
        result = await self.db.execute(
            select(func.avg(DnsLog.response_time_ms))
        )
        val = result.scalar_one_or_none()
        return int(val) if val is not None else 0

    # ── Audit Logs ───────────────────────────────────────────────
    async def create_audit_log(
        self,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: str = None,
        changes: dict = None,
        source_ip: str = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes or {},
            source_ip=source_ip,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_audit_logs(
        self, offset: int = 0, limit: int = 50
    ) -> tuple[list[AuditLog], int]:
        total = (await self.db.execute(select(func.count(AuditLog.id)))).scalar_one()
        result = await self.db.execute(
            select(AuditLog).order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    # ── Stats ────────────────────────────────────────────────────
    async def get_dns_query_count(self) -> int:
        result = await self.db.execute(select(func.count(DnsLog.id)))
        return result.scalar_one()

    async def get_blocked_query_count(self) -> int:
        result = await self.db.execute(
            select(func.count(DnsLog.id)).where(DnsLog.action == DnsAction.BLOCK)
        )
        return result.scalar_one()

    async def get_connection_count(self) -> int:
        result = await self.db.execute(
            select(func.count(DeviceLog.id)).where(
                DeviceLog.event_type == DeviceEventType.CONNECT
            )
        )
        return result.scalar_one()

    async def get_error_count(self) -> int:
        result = await self.db.execute(
            select(func.count(DeviceLog.id)).where(
                DeviceLog.event_type == DeviceEventType.ERROR
            )
        )
        return result.scalar_one()

    async def get_recent_events(self, limit: int = 10) -> list[DeviceLog]:
        result = await self.db.execute(
            select(DeviceLog).order_by(desc(DeviceLog.timestamp)).limit(limit)
        )
        return list(result.scalars().all())

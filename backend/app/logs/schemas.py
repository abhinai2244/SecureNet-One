"""
SecureNet One - Log Schemas
Pydantic models for log request/response validation.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Device Logs ──────────────────────────────────────────────────
class DeviceLogCreateRequest(BaseModel):
    device_id: UUID
    event_type: str = Field(..., pattern="^(connect|disconnect|heartbeat|error|posture|key_rotation)$")
    payload: Optional[dict[str, Any]] = None


class DeviceLogResponse(BaseModel):
    id: UUID
    device_id: UUID
    event_type: str
    payload: Optional[dict[str, Any]] = None
    source_ip: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── DNS Logs ─────────────────────────────────────────────────────
class DnsLogResponse(BaseModel):
    id: UUID
    device_id: Optional[UUID] = None
    query_name: str
    query_type: str
    response_code: Optional[str] = None
    action: str
    policy_id: Optional[UUID] = None
    response_time_ms: Optional[int] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── Audit Logs ───────────────────────────────────────────────────
class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    changes: Optional[dict[str, Any]] = None
    source_ip: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── List Responses ───────────────────────────────────────────────
class DeviceLogListResponse(BaseModel):
    logs: list[DeviceLogResponse]
    total: int
    page: int
    page_size: int


class DnsLogListResponse(BaseModel):
    logs: list[DnsLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class LogStatsResponse(BaseModel):
    """Log statistics for dashboard."""
    total_dns_queries: int
    blocked_queries: int
    total_connections: int
    total_errors: int
    top_blocked_domains: list[dict[str, Any]]
    recent_events: list[DeviceLogResponse]

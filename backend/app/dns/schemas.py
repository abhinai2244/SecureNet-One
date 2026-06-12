"""
SecureNet One - DNS Schemas
Pydantic models for DNS-over-HTTPS operations.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class DnsQueryRequest(BaseModel):
    """Manual DNS query request (for testing)."""
    name: str
    type: str = "A"
    device_id: Optional[UUID] = None


class DnsQueryResponse(BaseModel):
    """DNS query response."""
    name: str
    type: str
    answers: list[dict[str, Any]]
    action: str  # allow, block, redirect
    response_time_ms: int
    policy_applied: Optional[str] = None


class DnsFilterListResponse(BaseModel):
    """Current DNS filter lists."""
    blocked_domains: list[str]
    blocked_categories: list[str]
    total_rules: int

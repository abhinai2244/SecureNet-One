"""
SecureNet One - DNS Router
DNS-over-HTTPS endpoints implementing RFC 8484.
"""

import base64
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.security import require_admin
from app.dns.schemas import DnsFilterListResponse, DnsQueryRequest, DnsQueryResponse
from app.dns.service import DnsService
from app.shared.dependencies import CurrentUserId, DbSession

router = APIRouter(prefix="/dns", tags=["DNS"])


@router.get("/dns-query")
async def doh_get(
    request: Request,
    db: DbSession,
    dns: str = Query(..., description="Base64url-encoded DNS query"),
):
    """DNS-over-HTTPS GET endpoint (RFC 8484).
    The 'dns' query parameter contains a base64url-encoded DNS message.
    """
    # Decode base64url DNS query
    # Add padding if needed
    padding = 4 - len(dns) % 4
    if padding != 4:
        dns += "=" * padding
    dns_wire = base64.urlsafe_b64decode(dns)

    service = DnsService(db)
    response_wire = await service.resolve_doh_wireformat(dns_wire)

    return Response(
        content=response_wire,
        media_type="application/dns-message",
        headers={"Cache-Control": "max-age=300"},
    )


@router.post("/dns-query")
async def doh_post(
    request: Request,
    db: DbSession,
):
    """DNS-over-HTTPS POST endpoint (RFC 8484).
    Request body is raw DNS wire-format message.
    """
    dns_wire = await request.body()

    service = DnsService(db)
    response_wire = await service.resolve_doh_wireformat(dns_wire)

    return Response(
        content=response_wire,
        media_type="application/dns-message",
        headers={"Cache-Control": "max-age=300"},
    )


@router.post("/query", response_model=DnsQueryResponse)
async def dns_query(
    data: DnsQueryRequest,
    user_id: CurrentUserId,
    db: DbSession,
):
    """Human-readable DNS query endpoint for testing and dashboard."""
    service = DnsService(db)
    result = await service.resolve_query(
        data.name, data.type, str(data.device_id) if data.device_id else None
    )
    return DnsQueryResponse(**result)


@router.get("/filters", response_model=DnsFilterListResponse)
async def get_dns_filters(
    db: DbSession,
    _admin_id: str = Depends(require_admin),
):
    """Get current DNS filter lists (admin only)."""
    service = DnsService(db)
    result = await service.get_filter_lists()
    return DnsFilterListResponse(**result)

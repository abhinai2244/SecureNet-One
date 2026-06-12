"""
SecureNet One - Policy Router
API endpoints for policy management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import require_admin
from app.policies.schemas import (
    PolicyCreateRequest,
    PolicyListResponse,
    PolicyResponse,
    PolicyUpdateRequest,
)
from app.policies.service import PolicyService
from app.shared.dependencies import DbSession, Pagination

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    db: DbSession,
    pagination: Pagination,
    type: Optional[str] = Query(None, regex="^(dns|tunnel|access|posture)$"),
    _admin_id: str = Depends(require_admin),
):
    """List all policies with optional type filtering (admin only)."""
    service = PolicyService(db)
    policies, total = await service.list_policies(
        pagination.offset, pagination.limit, type
    )
    return PolicyListResponse(
        policies=policies,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    data: PolicyCreateRequest,
    db: DbSession,
    admin_id: str = Depends(require_admin),
):
    """Create a new policy (admin only)."""
    service = PolicyService(db)
    return await service.create_policy(data, admin_id)


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    db: DbSession,
    _admin_id: str = Depends(require_admin),
):
    """Get a specific policy by ID (admin only)."""
    service = PolicyService(db)
    return await service.get_policy(policy_id)


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    data: PolicyUpdateRequest,
    db: DbSession,
    _admin_id: str = Depends(require_admin),
):
    """Update a policy (admin only)."""
    service = PolicyService(db)
    return await service.update_policy(policy_id, data)


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    db: DbSession,
    _admin_id: str = Depends(require_admin),
):
    """Delete a policy (admin only)."""
    service = PolicyService(db)
    await service.delete_policy(policy_id)

"""
SecureNet One - Policy Service
Business logic for policy management.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.policies.models import PolicyType
from app.policies.repository import PolicyRepository
from app.policies.schemas import (
    PolicyCreateRequest,
    PolicyResponse,
    PolicyUpdateRequest,
)
from app.shared.exceptions import NotFoundException


class PolicyService:
    """Service for policy business logic."""

    def __init__(self, db: AsyncSession):
        self.repo = PolicyRepository(db)

    async def create_policy(
        self, data: PolicyCreateRequest, created_by: str
    ) -> PolicyResponse:
        policy = await self.repo.create(
            created_by=UUID(created_by),
            name=data.name,
            description=data.description,
            type=PolicyType(data.type),
            rules=data.rules,
            enabled=data.enabled,
            priority=data.priority,
        )
        return PolicyResponse.model_validate(policy)

    async def update_policy(
        self, policy_id: str, data: PolicyUpdateRequest
    ) -> PolicyResponse:
        policy = await self.repo.get_by_id(UUID(policy_id))
        if not policy:
            raise NotFoundException("Policy", policy_id)

        update_data = data.model_dump(exclude_unset=True)
        policy = await self.repo.update(policy, **update_data)
        return PolicyResponse.model_validate(policy)

    async def delete_policy(self, policy_id: str) -> None:
        policy = await self.repo.get_by_id(UUID(policy_id))
        if not policy:
            raise NotFoundException("Policy", policy_id)
        await self.repo.delete(policy)

    async def get_policy(self, policy_id: str) -> PolicyResponse:
        policy = await self.repo.get_by_id(UUID(policy_id))
        if not policy:
            raise NotFoundException("Policy", policy_id)
        return PolicyResponse.model_validate(policy)

    async def list_policies(
        self, offset: int = 0, limit: int = 20, type_filter: str = None
    ) -> tuple[list[PolicyResponse], int]:
        type_enum = PolicyType(type_filter) if type_filter else None
        policies, total = await self.repo.get_all(offset, limit, type_enum)
        return [PolicyResponse.model_validate(p) for p in policies], total

    async def get_active_dns_policies(self) -> list[PolicyResponse]:
        """Get active DNS policies for filtering."""
        policies = await self.repo.get_active_by_type(PolicyType.DNS)
        return [PolicyResponse.model_validate(p) for p in policies]

    def evaluate_dns_policy(self, domain: str, policies: list[PolicyResponse]) -> str:
        """Evaluate DNS policies against a domain. Returns 'allow' or 'block'."""
        for policy in policies:
            rules = policy.rules
            blocked_domains = rules.get("blocked_domains", [])
            blocked_categories = rules.get("blocked_categories", [])

            # Check exact domain match
            if domain in blocked_domains:
                return "block"

            # Check wildcard matches
            for blocked in blocked_domains:
                if blocked.startswith("*.") and domain.endswith(blocked[1:]):
                    return "block"

        return "allow"

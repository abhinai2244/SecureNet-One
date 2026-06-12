"""
SecureNet One - Policy Repository
Database access layer for policy operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.policies.models import Policy, PolicyType


class PolicyRepository:
    """Repository for policy database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, policy_id: UUID) -> Optional[Policy]:
        result = await self.db.execute(select(Policy).where(Policy.id == policy_id))
        return result.scalar_one_or_none()

    async def create(self, created_by: UUID = None, **kwargs) -> Policy:
        policy = Policy(created_by=created_by, **kwargs)
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def update(self, policy: Policy, **kwargs) -> Policy:
        for key, value in kwargs.items():
            if hasattr(policy, key) and value is not None:
                setattr(policy, key, value)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def delete(self, policy: Policy):
        await self.db.delete(policy)
        await self.db.flush()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        type_filter: Optional[PolicyType] = None,
    ) -> tuple[list[Policy], int]:
        query = select(Policy)
        count_query = select(func.count(Policy.id))

        if type_filter:
            query = query.where(Policy.type == type_filter)
            count_query = count_query.where(Policy.type == type_filter)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Policy.priority.asc()).offset(offset).limit(limit)
        )
        policies = list(result.scalars().all())
        return policies, total

    async def get_active_by_type(self, policy_type: PolicyType) -> list[Policy]:
        """Get all active policies of a specific type, ordered by priority."""
        result = await self.db.execute(
            select(Policy)
            .where(Policy.type == policy_type, Policy.enabled == True)
            .order_by(Policy.priority.asc())
        )
        return list(result.scalars().all())

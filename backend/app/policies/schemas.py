"""
SecureNet One - Policy Schemas
Pydantic models for policy request/response validation.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PolicyCreateRequest(BaseModel):
    """Schema for creating a policy."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: str = Field(..., pattern="^(dns|tunnel|access|posture)$")
    rules: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    priority: int = Field(default=100, ge=1, le=1000)


class PolicyUpdateRequest(BaseModel):
    """Schema for updating a policy."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rules: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)


class PolicyResponse(BaseModel):
    """Policy response."""
    id: UUID
    name: str
    description: Optional[str] = None
    type: str
    rules: dict[str, Any]
    enabled: bool
    priority: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyListResponse(BaseModel):
    """Paginated list of policies."""
    policies: list[PolicyResponse]
    total: int
    page: int
    page_size: int

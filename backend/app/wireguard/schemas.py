"""
SecureNet One - WireGuard Schemas
Pydantic models for WireGuard configuration.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WireGuardConfigResponse(BaseModel):
    """WireGuard client configuration for the agent."""
    interface_private_key: str
    interface_address: str
    interface_dns: str
    interface_mtu: int = 1420
    peer_public_key: str
    peer_endpoint: str
    peer_allowed_ips: str
    peer_persistent_keepalive: int = 25
    peer_preshared_key: Optional[str] = None


class WireGuardPeerResponse(BaseModel):
    """WireGuard peer info response."""
    id: UUID
    device_id: UUID
    public_key: str
    allowed_ips: str
    endpoint: Optional[str] = None
    persistent_keepalive: int
    last_handshake: Optional[datetime] = None
    tx_bytes: int = 0
    rx_bytes: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class WireGuardStatusResponse(BaseModel):
    """Overall WireGuard tunnel status."""
    server_public_key: str
    server_endpoint: str
    total_peers: int
    active_peers: int
    peers: list[WireGuardPeerResponse]


class KeyRotationResponse(BaseModel):
    """Response after key rotation."""
    message: str
    new_public_key: str
    config: WireGuardConfigResponse

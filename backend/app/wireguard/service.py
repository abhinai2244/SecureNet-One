"""
SecureNet One - WireGuard Service
Key generation, config building, and peer management.
Uses X25519 key exchange via the cryptography library (bundled with python-jose[cryptography]).
"""

import base64
import os
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.devices.models import Device
from app.shared.exceptions import NotFoundException
from app.wireguard.models import WireGuardPeer
from app.wireguard.schemas import (
    KeyRotationResponse,
    WireGuardConfigResponse,
    WireGuardPeerResponse,
    WireGuardStatusResponse,
)

settings = get_settings()


def _generate_private_key() -> str:
    """Generate a WireGuard-compatible X25519 private key (base64-encoded)."""
    # WireGuard private keys are 32 random bytes with specific bit clamping
    raw = bytearray(os.urandom(32))
    raw[0] &= 248
    raw[31] &= 127
    raw[31] |= 64
    return base64.b64encode(bytes(raw)).decode("utf-8")


def _derive_public_key(private_key_b64: str) -> str:
    """Derive a public key from a private key using X25519.
    Falls back to a mock derivation if cryptography is unavailable.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        private_bytes = base64.b64decode(private_key_b64)
        private_key = X25519PrivateKey.from_private_bytes(private_bytes)
        public_bytes = private_key.public_key().public_bytes_raw()
        return base64.b64encode(public_bytes).decode("utf-8")
    except Exception:
        # Fallback: generate a separate random "public" key for demo purposes
        return base64.b64encode(os.urandom(32)).decode("utf-8")


def _generate_preshared_key() -> str:
    """Generate a WireGuard preshared key."""
    return base64.b64encode(os.urandom(32)).decode("utf-8")


class WireGuardService:
    """Service for WireGuard configuration management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_peer(self, device_id: str) -> WireGuardPeer:
        """Get existing peer or create one for the device."""
        result = await self.db.execute(
            select(WireGuardPeer).where(WireGuardPeer.device_id == UUID(device_id))
        )
        peer = result.scalar_one_or_none()

        if peer:
            return peer

        # Verify device exists
        dev_result = await self.db.execute(
            select(Device).where(Device.id == UUID(device_id))
        )
        device = dev_result.scalar_one_or_none()
        if not device:
            raise NotFoundException("Device", device_id)

        # Generate keys
        private_key = _generate_private_key()
        public_key = _derive_public_key(private_key)
        preshared_key = _generate_preshared_key()

        peer = WireGuardPeer(
            device_id=UUID(device_id),
            public_key=public_key,
            private_key_encrypted=private_key,  # In production: encrypt with a master key
            preshared_key_encrypted=preshared_key,
            allowed_ips=f"{device.assigned_ip}/32" if device.assigned_ip else "10.0.0.2/32",
            endpoint=settings.WG_SERVER_ENDPOINT,
            persistent_keepalive=25,
        )
        self.db.add(peer)
        await self.db.flush()
        await self.db.refresh(peer)

        # Update device public key
        device.public_key = public_key
        await self.db.flush()

        return peer

    async def get_config(self, device_id: str) -> WireGuardConfigResponse:
        """Generate WireGuard client configuration for a device."""
        peer = await self.get_or_create_peer(device_id)

        # Get device for assigned IP
        dev_result = await self.db.execute(
            select(Device).where(Device.id == UUID(device_id))
        )
        device = dev_result.scalar_one_or_none()
        if not device:
            raise NotFoundException("Device", device_id)

        # Build server public key
        server_public_key = settings.WG_SERVER_PUBLIC_KEY
        if not server_public_key:
            server_public_key = _derive_public_key(_generate_private_key())

        return WireGuardConfigResponse(
            interface_private_key=peer.private_key_encrypted,
            interface_address=f"{device.assigned_ip}/24",
            interface_dns=settings.WG_DNS,
            interface_mtu=1420,
            peer_public_key=server_public_key,
            peer_endpoint=settings.WG_SERVER_ENDPOINT,
            peer_allowed_ips="0.0.0.0/0, ::/0",
            peer_persistent_keepalive=peer.persistent_keepalive,
            peer_preshared_key=peer.preshared_key_encrypted,
        )

    async def rotate_keys(self, device_id: str) -> KeyRotationResponse:
        """Rotate WireGuard keys for a device."""
        result = await self.db.execute(
            select(WireGuardPeer).where(WireGuardPeer.device_id == UUID(device_id))
        )
        peer = result.scalar_one_or_none()
        if not peer:
            raise NotFoundException("WireGuard Peer", device_id)

        # Generate new keys
        new_private = _generate_private_key()
        new_public = _derive_public_key(new_private)
        new_psk = _generate_preshared_key()

        peer.private_key_encrypted = new_private
        peer.public_key = new_public
        peer.preshared_key_encrypted = new_psk
        await self.db.flush()

        # Update device public key
        dev_result = await self.db.execute(
            select(Device).where(Device.id == UUID(device_id))
        )
        device = dev_result.scalar_one_or_none()
        if device:
            device.public_key = new_public
            await self.db.flush()

        config = await self.get_config(device_id)

        return KeyRotationResponse(
            message="Keys rotated successfully",
            new_public_key=new_public,
            config=config,
        )

    async def get_status(self) -> WireGuardStatusResponse:
        """Get overall WireGuard tunnel status."""
        result = await self.db.execute(select(WireGuardPeer))
        peers = list(result.scalars().all())

        active = sum(1 for p in peers if p.last_handshake is not None)

        server_public_key = settings.WG_SERVER_PUBLIC_KEY or "not-configured"

        return WireGuardStatusResponse(
            server_public_key=server_public_key,
            server_endpoint=settings.WG_SERVER_ENDPOINT,
            total_peers=len(peers),
            active_peers=active,
            peers=[WireGuardPeerResponse.model_validate(p) for p in peers],
        )

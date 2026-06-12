"""
SecureNet One - Redis Client
Connection management and utility functions for caching and session management.
"""

from typing import Optional

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# ── Redis Client ─────────────────────────────────────────────────
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis():
    """Close the Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# ── Token Blacklist ──────────────────────────────────────────────
async def blacklist_token(token_jti: str, expires_in: int):
    """Add a token to the blacklist (for logout)."""
    client = await get_redis()
    await client.setex(f"blacklist:{token_jti}", expires_in, "1")


async def is_token_blacklisted(token_jti: str) -> bool:
    """Check if a token is blacklisted."""
    client = await get_redis()
    result = await client.get(f"blacklist:{token_jti}")
    return result is not None


# ── Session Management ───────────────────────────────────────────
async def store_session(user_id: str, session_data: dict, ttl: int = 86400):
    """Store a user session in Redis."""
    client = await get_redis()
    import json
    await client.setex(f"session:{user_id}", ttl, json.dumps(session_data))


async def get_session(user_id: str) -> Optional[dict]:
    """Retrieve a user session from Redis."""
    client = await get_redis()
    import json
    data = await client.get(f"session:{user_id}")
    return json.loads(data) if data else None


async def delete_session(user_id: str):
    """Delete a user session from Redis."""
    client = await get_redis()
    await client.delete(f"session:{user_id}")


# ── Device Status Cache ──────────────────────────────────────────
async def set_device_online(device_id: str, ttl: int = 180):
    """Mark a device as online with TTL-based auto-expiry."""
    client = await get_redis()
    await client.setex(f"device:online:{device_id}", ttl, "1")


async def is_device_online(device_id: str) -> bool:
    """Check if a device is currently online."""
    client = await get_redis()
    result = await client.get(f"device:online:{device_id}")
    return result is not None


async def get_online_device_count() -> int:
    """Get the count of currently online devices."""
    client = await get_redis()
    keys = []
    async for key in client.scan_iter(match="device:online:*"):
        keys.append(key)
    return len(keys)

import redis.asyncio as aioredis

from core.settings import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


# ── OTP ──────────────────────────────────────────────────────────────────────


async def set_otp(email: str, code: str, ttl: int = 600):
    """Store OTP in Redis with a TTL (default 10 mins)."""
    await redis_client.setex(f"otp:{email}", ttl, code)


async def get_otp(email: str) -> str | None:
    """Retrieve OTP from Redis."""
    return await redis_client.get(f"otp:{email}")


async def delete_otp(email: str):
    """Delete OTP from Redis after verification."""
    await redis_client.delete(f"otp:{email}")


# ── WebAuthn Challenges ─────────────────────────────────────────────────────


async def set_challenge(email: str, challenge: bytes, ttl: int = 300):
    """Store WebAuthn challenge in Redis (5 mins TTL)."""
    await redis_client.setex(f"challenge:{email}", ttl, challenge.hex())


async def get_challenge(email: str) -> bytes | None:
    """Retrieve WebAuthn challenge from Redis."""
    val = await redis_client.get(f"challenge:{email}")
    return bytes.fromhex(val) if val else None


async def delete_challenge(email: str):
    """Delete challenge from Redis."""
    await redis_client.delete(f"challenge:{email}")


# ── Token Blacklist ──────────────────────────────────────────────────────────


async def blacklist_token(jti: str, ttl: int = 86400):
    """Add a token ID to the blacklist (default 24h TTL)."""
    await redis_client.setex(f"blacklist:{jti}", ttl, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a token has been revoked."""
    val = await redis_client.exists(f"blacklist:{jti}")
    return val > 0


# ── Rate Limiting ────────────────────────────────────────────────────────────


async def check_rate_limit(key: str, max_requests: int, window_seconds: int) -> bool:
    """
    Returns True if within limit, False if exceeded.
    Uses an atomic INCR-first pattern to prevent race conditions.
    """
    full_key = f"rate:{key}"
    current = await redis_client.incr(full_key)
    if current == 1:
        await redis_client.expire(full_key, window_seconds)
    return current <= max_requests

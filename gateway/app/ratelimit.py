import time
from fastapi import HTTPException, status
from .config import settings

try:
    from redis import asyncio as aioredis  # redis>=4 provides asyncio API
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore

_redis = None


async def _get_redis():
    global _redis
    if _redis is None and aioredis is not None:
        _redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis


_LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local rps = tonumber(ARGV[2])
local burst = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])
local state = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(state[1]) or burst
local ts = tonumber(state[2]) or now_ms
local delta = math.max(0, now_ms - ts)
local refill = (delta / 1000.0) * rps
tokens = math.min(burst, tokens + refill)
local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end
redis.call('HMSET', key, 'tokens', tokens, 'ts', now_ms)
redis.call('PEXPIRE', key, ttl)
return {allowed, tokens}
"""


async def check_rate_limit(key_id: str) -> None:
    client = await _get_redis()
    if client is None:
        # No Redis available; allow request
        return
    now_ms = int(time.time() * 1000)
    rps = settings.rate_limit_rps_default
    burst = settings.rate_limit_burst_default
    ttl_ms = max(2000, int(2000 + 1000 * burst / max(1, rps)))
    try:
        allowed, _ = await client.eval(_LUA_TOKEN_BUCKET, 1, f"rl:{key_id}", now_ms, rps, burst, ttl_ms)
        if int(allowed) != 1:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    except HTTPException:
        raise
    except Exception:
        # Fallback: allow on Redis errors
        return

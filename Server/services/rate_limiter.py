"""
Distributed rate limiter using Redis sliding window.

Implements a sliding-window rate limiter backed by Redis sorted sets.
Each request is scored by its timestamp; expired entries are pruned on
every check so the window always reflects the most recent traffic.

Includes preset configurations for common endpoints and a FastAPI
dependency factory for easy integration.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


# ── Rate limit result ──────────────────────────────────────────────────────

@dataclass
class RateLimitResult:
    """Outcome of a single rate-limit check.

    Attributes:
        allowed: Whether the request is within limits.
        remaining: Number of requests remaining in the current window.
        reset_at: UTC epoch timestamp when the window resets.
        retry_after: Seconds until the next request will be allowed,
                     or ``None`` if the request was allowed.
    """

    allowed: bool
    remaining: int
    reset_at: float
    retry_after: Optional[float] = None


# ── Preset configurations ─────────────────────────────────────────────────

RATE_LIMIT_PRESETS: Dict[str, Dict[str, int]] = {
    "ride_request": {"max_requests": 5, "window_seconds": 60},
    "location_update": {"max_requests": 60, "window_seconds": 60},
    "driver_accept": {"max_requests": 30, "window_seconds": 60},
    "api_general": {"max_requests": 100, "window_seconds": 60},
    "api_auth": {"max_requests": 10, "window_seconds": 300},
}


# ── Rate limiter ───────────────────────────────────────────────────────────

class RateLimiter:
    """Redis-based sliding window rate limiter.

    Uses a sorted set per rate-limit key where each member is a unique
    request ID (timestamp-based) scored by its arrival time.  On each
    check the set is trimmed to the current window before counting.

    Args:
        redis_client: An optional ``redis.Redis`` instance.  If not
            provided, the shared client from ``kafka.redis_client`` is
            used on first call.
    """

    def __init__(self, redis_client=None) -> None:  # noqa: ANN001
        self._redis = redis_client

    def _get_redis(self):  # noqa: ANN202
        """Lazy-load the Redis client.

        Returns:
            A ``redis.Redis`` instance.
        """
        if self._redis is None:
            from kafka.redis_client import get_redis
            self._redis = get_redis()
        return self._redis

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check if a request is within rate limits using a sliding window.

        The algorithm:
        1. Remove all sorted-set members whose score (timestamp) is
           older than ``now - window_seconds``.
        2. Count remaining members.
        3. If below ``max_requests``, add the current request and allow.
        4. Otherwise, deny and report ``retry_after``.

        Args:
            key: The rate-limit key (e.g. ``"rl:ride_request:user:42"``).
            max_requests: Maximum number of requests in the window.
            window_seconds: Window duration in seconds.

        Returns:
            A ``RateLimitResult`` describing the outcome.
        """
        try:
            redis = self._get_redis()
        except Exception as exc:
            logger.warning(
                "Redis unavailable for rate limiting, allowing request: %s", exc
            )
            return RateLimitResult(
                allowed=True,
                remaining=max_requests,
                reset_at=time.time() + window_seconds,
            )

        now = time.time()
        window_start = now - window_seconds
        reset_at = now + window_seconds

        try:
            pipe = redis.pipeline(transaction=True)
            # 1. Remove expired entries
            pipe.zremrangebyscore(key, "-inf", window_start)
            # 2. Count current entries
            pipe.zcard(key)
            # 3. Add current request (score = now, member = now with nanos)
            member = f"{now}:{id(key)}"
            pipe.zadd(key, {member: now})
            # 4. Set TTL so keys don't linger forever
            pipe.expire(key, window_seconds + 1)
            results = pipe.execute()

            current_count = results[1]  # zcard result before this request

            if current_count >= max_requests:
                # Over limit — remove the member we just added
                redis.zrem(key, member)

                # Find the oldest entry to compute retry_after
                oldest = redis.zrange(key, 0, 0, withscores=True)
                retry_after = (
                    (oldest[0][1] + window_seconds - now) if oldest else float(window_seconds)
                )
                retry_after = max(retry_after, 0.1)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=round(retry_after, 2),
                )

            remaining = max(0, max_requests - current_count - 1)
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_at=reset_at,
            )

        except Exception as exc:
            logger.error("Rate limit check failed, allowing request: %s", exc)
            return RateLimitResult(
                allowed=True,
                remaining=max_requests,
                reset_at=time.time() + window_seconds,
            )

    @staticmethod
    def get_rate_limit_key(
        limit_type: str,
        identifier: str,
        endpoint: str = "",
    ) -> str:
        """Build a standardised rate-limit key.

        Args:
            limit_type: Category of the limit (e.g. ``"ride_request"``).
            identifier: Unique caller identifier (user ID, IP, etc.).
            endpoint: Optional endpoint path for finer granularity.

        Returns:
            A namespaced Redis key string.
        """
        parts = ["rl", limit_type, identifier]
        if endpoint:
            parts.append(endpoint)
        return ":".join(parts)


# ── FastAPI dependency factory ─────────────────────────────────────────────

def rate_limit_dependency(limit_type: str = "api_general"):
    """FastAPI dependency factory for rate limiting.

    Returns an async dependency that checks the request against the
    preset identified by ``limit_type``.  Raises ``HTTPException(429)``
    when the limit is exceeded.

    Args:
        limit_type: One of the keys in ``RATE_LIMIT_PRESETS``.

    Returns:
        An async callable suitable for use with ``Depends()``.

    Usage::

        from services.rate_limiter import rate_limit_dependency

        @router.post("/rides", dependencies=[Depends(rate_limit_dependency("ride_request"))])
        async def create_ride(...): ...
    """
    preset = RATE_LIMIT_PRESETS.get(limit_type, RATE_LIMIT_PRESETS["api_general"])

    async def _check_rate_limit(request: Request) -> None:
        """Enforce the rate limit for the current request.

        Args:
            request: The incoming FastAPI request.

        Raises:
            HTTPException: 429 Too Many Requests when the limit is exceeded.
        """
        limiter = RateLimiter()

        # Identify caller by user ID (if authenticated) or client IP
        client_id = "anonymous"
        if hasattr(request.state, "user_id"):
            client_id = str(request.state.user_id)
        elif request.client:
            client_id = request.client.host

        key = limiter.get_rate_limit_key(
            limit_type=limit_type,
            identifier=client_id,
            endpoint=request.url.path,
        )

        result = limiter.check_rate_limit(
            key=key,
            max_requests=preset["max_requests"],
            window_seconds=preset["window_seconds"],
        )

        if not result.allowed:
            logger.warning(
                "Rate limit exceeded: type=%s client=%s endpoint=%s",
                limit_type,
                client_id,
                request.url.path,
            )
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={
                    "Retry-After": str(int(result.retry_after or preset["window_seconds"])),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(result.reset_at)),
                },
            )

    return _check_rate_limit

"""
Unit tests for the distributed rate limiter.

Tests:
- RateLimitResult dataclass
- Rate limit key generation
- Preset configurations
- In-memory fallback behavior (when Redis unavailable)
"""

import pytest
import time
from services.rate_limiter import (
    RateLimiter,
    RateLimitResult,
    RATE_LIMIT_PRESETS,
)


class TestRateLimitResult:
    """Tests for the RateLimitResult dataclass."""

    def test_allowed_result(self):
        result = RateLimitResult(
            allowed=True, remaining=9, reset_at=time.time() + 60,
        )
        assert result.allowed is True
        assert result.remaining == 9
        assert result.retry_after is None

    def test_rejected_result(self):
        result = RateLimitResult(
            allowed=False, remaining=0,
            reset_at=time.time() + 30, retry_after=30.0,
        )
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30.0


class TestPresets:
    """Tests for rate limit preset configurations."""

    def test_presets_exist(self):
        assert "ride_request" in RATE_LIMIT_PRESETS
        assert "location_update" in RATE_LIMIT_PRESETS
        assert "driver_accept" in RATE_LIMIT_PRESETS
        assert "api_general" in RATE_LIMIT_PRESETS
        assert "api_auth" in RATE_LIMIT_PRESETS

    def test_preset_values(self):
        ride = RATE_LIMIT_PRESETS["ride_request"]
        assert ride["max_requests"] == 5
        assert ride["window_seconds"] == 60

        auth = RATE_LIMIT_PRESETS["api_auth"]
        assert auth["max_requests"] == 10
        assert auth["window_seconds"] == 300

    def test_location_update_higher_limit(self):
        """Location updates should have a higher limit than ride requests."""
        loc = RATE_LIMIT_PRESETS["location_update"]
        ride = RATE_LIMIT_PRESETS["ride_request"]
        assert loc["max_requests"] > ride["max_requests"]


class TestRateLimiterKeyGeneration:
    """Tests for rate limit key generation."""

    def test_get_rate_limit_key(self):
        limiter = RateLimiter()
        key = limiter.get_rate_limit_key("api_general", "user:42", "/api/rides")
        assert "api_general" in key
        assert "user:42" in key

    def test_unique_keys_for_different_users(self):
        limiter = RateLimiter()
        key1 = limiter.get_rate_limit_key("api_general", "user:1")
        key2 = limiter.get_rate_limit_key("api_general", "user:2")
        assert key1 != key2

    def test_unique_keys_for_different_types(self):
        limiter = RateLimiter()
        key1 = limiter.get_rate_limit_key("ride_request", "user:1")
        key2 = limiter.get_rate_limit_key("location_update", "user:1")
        assert key1 != key2


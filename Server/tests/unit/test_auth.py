"""
Unit tests for authentication logic (JWT generation and validation).
RED PHASE: These tests capture required behavior before/after Bug #4, #8 fixes.
"""
import os
import pytest
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "test-secret-key-for-testing-only"


class TestJWTTokenGeneration:
    """Tests for token generation behavior."""

    def test_access_token_has_correct_role_user(self):
        token = jwt.encode(
            {"sub": "42", "role": "user", "type": "access",
             "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
            SECRET_KEY, algorithm="HS256"
        )
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert payload["role"] == "user"
        assert payload["sub"] == "42"

    def test_refresh_token_has_type_refresh(self):
        token = jwt.encode(
            {"sub": "42", "role": "driver", "type": "refresh",
             "exp": datetime.now(timezone.utc) + timedelta(days=30)},
            SECRET_KEY, algorithm="HS256"
        )
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert payload["type"] == "refresh"


class TestGetCurrentDriverAuthGuard:
    """
    Tests for get_current_driver (Bug #8: missing type check).
    """

    def test_driver_access_token_should_be_rejected_by_refresh_guard(self):
        """
        An access token (type='access') must NOT authenticate driver-protected
        endpoints that expect a refresh token cookie. This was Bug #8.
        """
        from auth.dependencies import get_current_driver
        from fastapi import HTTPException

        # Create an access token (not a refresh token) for a driver
        access_token = jwt.encode(
            {
                "sub": "1",
                "role": "driver",
                "type": "access",  # NOT refresh
                "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        # Patch the secret key used in the module
        import auth.dependencies as dep
        original_key = dep.SECRET_KEY
        dep.SECRET_KEY = SECRET_KEY

        try:
            with pytest.raises(HTTPException) as exc_info:
                get_current_driver(refresh_token=access_token)
            assert exc_info.value.status_code in (401, 403)
        finally:
            dep.SECRET_KEY = original_key

    def test_driver_refresh_token_authenticates_successfully(self):
        """A valid refresh token with role=driver must return the driver_id."""
        from auth.dependencies import get_current_driver
        import auth.dependencies as dep
        original_key = dep.SECRET_KEY
        dep.SECRET_KEY = SECRET_KEY

        refresh_token = jwt.encode(
            {
                "sub": "7",
                "role": "driver",
                "type": "refresh",
                "exp": datetime.now(timezone.utc) + timedelta(days=30)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        try:
            result = get_current_driver(refresh_token=refresh_token)
            assert result == 7
        finally:
            dep.SECRET_KEY = original_key

    def test_user_token_rejected_for_driver_endpoint(self):
        """A user refresh token must be rejected for driver endpoints."""
        from auth.dependencies import get_current_driver
        from fastapi import HTTPException
        import auth.dependencies as dep
        original_key = dep.SECRET_KEY
        dep.SECRET_KEY = SECRET_KEY

        user_token = jwt.encode(
            {
                "sub": "5",
                "role": "user",
                "type": "refresh",
                "exp": datetime.now(timezone.utc) + timedelta(days=30)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        try:
            with pytest.raises(HTTPException) as exc_info:
                get_current_driver(refresh_token=user_token)
            assert exc_info.value.status_code == 403
        finally:
            dep.SECRET_KEY = original_key

    def test_expired_token_raises_401(self):
        """Expired tokens must raise 401."""
        from auth.dependencies import get_current_driver
        from fastapi import HTTPException
        import auth.dependencies as dep
        original_key = dep.SECRET_KEY
        dep.SECRET_KEY = SECRET_KEY

        expired_token = jwt.encode(
            {
                "sub": "1",
                "role": "driver",
                "type": "refresh",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        try:
            with pytest.raises(HTTPException) as exc_info:
                get_current_driver(refresh_token=expired_token)
            assert exc_info.value.status_code == 401
        finally:
            dep.SECRET_KEY = original_key

    def test_no_cookie_raises_401(self):
        """Missing cookie must raise 401."""
        from auth.dependencies import get_current_driver
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_current_driver(refresh_token=None)
        assert exc_info.value.status_code == 401


class TestGetCurrentUserAuthGuard:
    """Tests for get_current_user."""

    def test_user_refresh_token_authenticates_successfully(self):
        from auth.dependencies import get_current_user
        import auth.dependencies as dep
        original_key = dep.SECRET_KEY
        dep.SECRET_KEY = SECRET_KEY

        refresh_token = jwt.encode(
            {
                "sub": "3",
                "role": "user",
                "type": "refresh",
                "exp": datetime.now(timezone.utc) + timedelta(days=30)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        try:
            result = get_current_user(refresh_token=refresh_token)
            assert result == 3
        finally:
            dep.SECRET_KEY = original_key

    def test_driver_token_rejected_for_user_endpoint(self):
        from auth.dependencies import get_current_user
        from fastapi import HTTPException
        import auth.dependencies as dep
        original_key = dep.SECRET_KEY
        dep.SECRET_KEY = SECRET_KEY

        driver_token = jwt.encode(
            {
                "sub": "2",
                "role": "driver",
                "type": "refresh",
                "exp": datetime.now(timezone.utc) + timedelta(days=30)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        try:
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(refresh_token=driver_token)
            assert exc_info.value.status_code == 403
        finally:
            dep.SECRET_KEY = original_key

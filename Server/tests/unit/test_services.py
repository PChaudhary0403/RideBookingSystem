"""
Unit tests for UserService business logic.
RED PHASE: Tests cover password hashing integration, login validation.
"""
import pytest
from unittest.mock import MagicMock, patch

# Import all SQLAlchemy models upfront so that the ORM mapper
# can resolve relationships (e.g., User.location → UserLocation)
# before any model is instantiated.
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

from UserSide.models.user_location import UserLocation   # noqa: F401
from DynamicDB.models.triprequest import TripRequest     # noqa: F401
from Trip.models.Trip import Trip                        # noqa: F401
from DriverSide.models.vehicle import Vehicle            # noqa: F401
from DriverSide.models.Driver import Rider               # noqa: F401  ← must be before TripRequest mapper init
from DynamicDB.models.Driver_Location import DriverLocation  # noqa: F401
from DynamicDB.models.active_riders import ActiveDriver   # noqa: F401
from Trip.models.ride_request import RideRequest          # noqa: F401


class TestUserServiceRegistration:
    """Tests for user registration with password hashing."""

    def test_register_user_stores_hashed_password(self):
        """Registration must store a hashed password, not plaintext."""
        from utils.security import verify_password

        stored_password = None

        def capture_add(user):
            nonlocal stored_password
            stored_password = user.password
            # Simulate DB refresh
            user.id = 1

        with patch("UserSide.repositories.user_repo.UserRepository.add", side_effect=capture_add):
            from UserSide.services.user_services import UserService
            service = UserService()
            service.register_user("Alice", "9999999999", "alice@example.com", "plaintextpassword")

        assert stored_password is not None
        assert stored_password != "plaintextpassword", "Password must not be stored as plaintext"
        assert verify_password("plaintextpassword", stored_password), "Stored hash must verify correctly"

    def test_register_user_returns_user_with_id(self):
        """register_user must return the created user object."""
        with patch("UserSide.repositories.user_repo.UserRepository.add") as mock_add:
            from UserSide.models.User import User

            def set_id(user):
                user.id = 42

            mock_add.side_effect = set_id
            from UserSide.services.user_services import UserService
            service = UserService()
            result = service.register_user("Bob", "8888888888", "bob@example.com", "pass123")
            assert result is not None


class TestUserServiceLogin:
    """Tests for user login with password verification."""

    def test_login_correct_password_returns_success(self):
        """Login with correct password must return success=True and user."""
        from utils.security import hash_password
        from UserSide.models.User import User

        mock_user = User()
        mock_user.id = 1
        mock_user.emailID = "alice@example.com"
        mock_user.password = hash_password("correctpass")

        with patch("UserSide.repositories.user_repo.UserRepository.find_by_email", return_value=mock_user):
            from UserSide.services.user_services import UserService
            service = UserService()
            result = service.login("alice@example.com", "correctpass")

        assert result["success"] is True
        assert result["user"] is mock_user

    def test_login_wrong_password_returns_failure(self):
        """Login with wrong password must return success=False."""
        from utils.security import hash_password
        from UserSide.models.User import User

        mock_user = User()
        mock_user.id = 1
        mock_user.emailID = "alice@example.com"
        mock_user.password = hash_password("correctpass")

        with patch("UserSide.repositories.user_repo.UserRepository.find_by_email", return_value=mock_user):
            from UserSide.services.user_services import UserService
            service = UserService()
            result = service.login("alice@example.com", "wrongpass")

        assert result["success"] is False
        assert result["error"] == "INVALID_PASSWORD"

    def test_login_user_not_found_returns_failure(self):
        """Login with nonexistent email must return USER_NOT_FOUND."""
        with patch("UserSide.repositories.user_repo.UserRepository.find_by_email", return_value=None):
            from UserSide.services.user_services import UserService
            service = UserService()
            result = service.login("nobody@example.com", "somepass")

        assert result["success"] is False
        assert result["error"] == "USER_NOT_FOUND"

    def test_login_plaintext_password_fails_against_hash(self):
        """Plaintext password stored by old system must not authenticate."""
        from UserSide.models.User import User

        mock_user = User()
        mock_user.id = 1
        mock_user.emailID = "old@example.com"
        mock_user.password = "plaintextpassword"  # Old plaintext record

        with patch("UserSide.repositories.user_repo.UserRepository.find_by_email", return_value=mock_user):
            from UserSide.services.user_services import UserService
            service = UserService()
            result = service.login("old@example.com", "plaintextpassword")

        # After the fix, plaintext comparison is gone — verification against a
        # non-bcrypt string must fail safely
        assert result["success"] is False


class TestDriverServiceLogin:
    """Tests for driver login with password verification."""

    def test_driver_login_correct_password_returns_success(self):
        from utils.security import hash_password
        from DriverSide.models.Driver import Rider

        mock_driver = Rider()
        mock_driver.id = 5
        mock_driver.email = "driver@example.com"
        mock_driver.password = hash_password("driverpass")

        with patch("DriverSide.repositories.rider_repo.RiderRepository.find_by_email", return_value=mock_driver), \
             patch("DynamicDB.repositories.active_rider_repo.ActiveDriverRepository.upsert"):
            from DriverSide.services.rider_services import RiderService
            service = RiderService()
            result = service.login("driver@example.com", "driverpass")

        assert result["success"] is True
        assert result["rider"] is mock_driver

    def test_driver_login_wrong_password_fails(self):
        from utils.security import hash_password
        from DriverSide.models.Driver import Rider

        mock_driver = Rider()
        mock_driver.id = 5
        mock_driver.email = "driver@example.com"
        mock_driver.password = hash_password("driverpass")

        with patch("DriverSide.repositories.rider_repo.RiderRepository.find_by_email", return_value=mock_driver):
            from DriverSide.services.rider_services import RiderService
            service = RiderService()
            result = service.login("driver@example.com", "wrongpass")

        assert result["success"] is False
        assert result["error"] == "INVALID_PASSWORD"

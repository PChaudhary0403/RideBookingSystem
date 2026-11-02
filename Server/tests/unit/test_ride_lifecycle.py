"""
Unit tests for the RideLifecycleService.

Tests:
- Ride request creation with outbox event
- Accept with race condition protection
- Reject with status reset
- Cancel with driver release
- Start and complete lifecycle
- Invalid state transition rejection
"""

import pytest
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from datetime import datetime, timezone

from DataBase.Connection import Base, engine, SessionLocal
from DynamicDB.models.triprequest import TripRequest
from DynamicDB.models.active_riders import ActiveDriver
from DynamicDB.models.Driver_Location import DriverLocation
from kafka.outbox.models import OutboxEvent, ProcessedEvent
from services.ride_service import RideLifecycleService


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop after."""
    # Import all models so Base.metadata knows about them
    from UserSide.models.User import User  # noqa: F401
    from UserSide.models.user_location import UserLocation  # noqa: F401
    from DriverSide.models.Driver import Rider  # noqa: F401
    from DriverSide.models.vehicle import Vehicle  # noqa: F401
    from Trip.models.Trip import Trip  # noqa: F401
    from Trip.models.ride_request import RideRequest  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed_driver(db):
    """Create a minimal driver + active driver record for testing."""
    from DriverSide.models.Driver import Rider

    rider = Rider(
        name="Test", surname="Driver",
        email="test@driver.com", phone="1234567890",
        password="hashed", address="Test St", licenceno="DL001",
    )
    db.add(rider)
    db.flush()

    active = ActiveDriver(
        driver_id=rider.id,
        is_online=True,
        is_available=True,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(active)

    location = DriverLocation(
        driver_id=rider.id,
        latitude=19.076,
        longitude=72.877,
    )
    db.add(location)

    db.commit()
    return rider.id


@pytest.fixture
def seed_user(db):
    """Create a minimal user record for testing."""
    from UserSide.models.User import User

    user = User(
        name="Test User",
        phone="9876543210",
        emailID="test@user.com",
        password="hashed",
    )
    db.add(user)
    db.commit()
    return user.id


class TestRideRequest:
    """Tests for ride request creation."""

    def test_request_ride_creates_trip_and_outbox(self, db, seed_user, seed_driver):
        trip = RideLifecycleService.request_ride(
            db=db,
            user_id=seed_user,
            driver_id=seed_driver,
            pickup_lat=19.076,
            pickup_long=72.877,
            dest_lat=19.229,
            dest_long=72.856,
        )

        assert trip.id is not None
        assert trip.status == "pending"
        assert trip.user_id == seed_user
        assert trip.driver_id == seed_driver

        # Verify outbox event was created
        outbox = db.query(OutboxEvent).filter_by(
            aggregate_id=str(trip.id),
        ).first()
        assert outbox is not None
        assert outbox.event_type == "ride.requested"
        assert outbox.status == "pending"
        assert outbox.topic == "ridebooking.rides.v1"

    def test_request_ride_outbox_payload(self, db, seed_user, seed_driver):
        trip = RideLifecycleService.request_ride(
            db=db,
            user_id=seed_user,
            driver_id=seed_driver,
            pickup_lat=19.076,
            pickup_long=72.877,
            dest_lat=19.229,
            dest_long=72.856,
        )

        outbox = db.query(OutboxEvent).filter_by(
            aggregate_id=str(trip.id),
        ).first()

        payload = outbox.payload
        assert payload["event_type"] == "ride.requested"
        assert payload["payload"]["ride_id"] == trip.id
        assert payload["payload"]["user_id"] == seed_user


class TestRideAccept:
    """Tests for ride acceptance."""

    def _create_assigned_ride(self, db, user_id, driver_id):
        """Create a ride in 'assigned' status (DRIVER_ASSIGNED), ready for acceptance."""
        trip = TripRequest(
            user_id=user_id,
            driver_id=driver_id,
            pickup_lat=19.0, pickup_long=72.0,
            dest_lat=19.1, dest_long=72.1,
            status="assigned",
        )
        db.add(trip)
        db.commit()
        return trip

    def test_accept_ride(self, db, seed_user, seed_driver):
        trip = self._create_assigned_ride(db, seed_user, seed_driver)

        result = RideLifecycleService.accept_ride(db, trip.id, seed_driver)
        assert result.status == "accepted"

        # Driver should be marked unavailable
        active = db.query(ActiveDriver).filter_by(driver_id=seed_driver).first()
        assert active.is_available is False

        # Outbox event should exist
        outbox = db.query(OutboxEvent).filter_by(
            event_type="ride.driver.accepted",
        ).first()
        assert outbox is not None

    def test_accept_already_accepted_ride_fails(self, db, seed_user, seed_driver):
        trip = self._create_assigned_ride(db, seed_user, seed_driver)
        trip.status = "accepted"
        db.commit()

        with pytest.raises(ValueError, match="Invalid status transition"):
            RideLifecycleService.accept_ride(db, trip.id, seed_driver)

    def test_accept_nonexistent_ride_fails(self, db, seed_driver):
        with pytest.raises(ValueError, match="not found"):
            RideLifecycleService.accept_ride(db, 999, seed_driver)


class TestRideReject:
    """Tests for ride rejection."""

    def test_reject_ride(self, db, seed_user, seed_driver):
        trip = TripRequest(
            user_id=seed_user, driver_id=seed_driver,
            pickup_lat=19.0, pickup_long=72.0,
            dest_lat=19.1, dest_long=72.1,
            status="pending",
        )
        db.add(trip)
        db.commit()

        result = RideLifecycleService.reject_ride(db, trip.id, seed_driver)
        assert result.status == "pending"

        outbox = db.query(OutboxEvent).filter_by(
            event_type="ride.driver.rejected",
        ).first()
        assert outbox is not None


class TestRideCancel:
    """Tests for ride cancellation."""

    def test_cancel_ride_releases_driver(self, db, seed_user, seed_driver):
        trip = TripRequest(
            user_id=seed_user, driver_id=seed_driver,
            pickup_lat=19.0, pickup_long=72.0,
            dest_lat=19.1, dest_long=72.1,
            status="pending",
        )
        db.add(trip)
        db.commit()

        # Mark driver unavailable first
        active = db.query(ActiveDriver).filter_by(driver_id=seed_driver).first()
        active.is_available = False
        db.commit()

        result = RideLifecycleService.cancel_ride(db, trip.id, seed_user)
        assert result.status == "cancelled"

        # Driver should be available again
        db.refresh(active)
        assert active.is_available is True

    def test_cancel_completed_ride_fails(self, db, seed_user, seed_driver):
        trip = TripRequest(
            user_id=seed_user, driver_id=seed_driver,
            pickup_lat=19.0, pickup_long=72.0,
            dest_lat=19.1, dest_long=72.1,
            status="completed",
        )
        db.add(trip)
        db.commit()

        with pytest.raises(ValueError, match="Invalid status transition"):
            RideLifecycleService.cancel_ride(db, trip.id, seed_user)


class TestRideComplete:
    """Tests for ride completion."""

    def test_complete_ride(self, db, seed_user, seed_driver):
        trip = TripRequest(
            user_id=seed_user, driver_id=seed_driver,
            pickup_lat=19.0, pickup_long=72.0,
            dest_lat=19.1, dest_long=72.1,
            status="in_progress",
        )
        db.add(trip)
        db.commit()

        result = RideLifecycleService.complete_ride(db, trip.id, seed_driver)
        assert result.status == "completed"

        # Driver should be available again
        active = db.query(ActiveDriver).filter_by(driver_id=seed_driver).first()
        assert active.is_available is True

        outbox = db.query(OutboxEvent).filter_by(
            event_type="ride.completed",
        ).first()
        assert outbox is not None


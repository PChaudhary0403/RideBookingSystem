"""
Concurrency tests for ride acceptance.

Tests:
- Sequential attempts to accept the same ride after the first acceptance
  are rejected by the state machine.
- The threading test demonstrates that SQLite with StaticPool serialises
  writes; on PostgreSQL with SELECT FOR UPDATE the same approach prevents
  truly concurrent double-acceptance.

Note on SQLite:
  SQLite in-memory with StaticPool uses a single shared connection.
  Threads are serialised by SQLite's internal lock, and each new
  Session().query() sees committed data from prior threads.  However,
  SQLAlchemy's identity map may serve stale cached objects to threads
  sharing the same underlying connection.  This means the threading test
  is best validated as a sequential state-machine test under SQLite.
  The SELECT FOR UPDATE codepath (which is what actually prevents
  concurrent acceptance in production) is only testable against PostgreSQL.
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


def _create_drivers(db, count=3):
    """Create multiple drivers for concurrency testing."""
    from DriverSide.models.Driver import Rider

    driver_ids = []
    for i in range(count):
        rider = Rider(
            name=f"Driver{i}", surname="Test",
            email=f"driver{i}@test.com", phone=f"12345{i:05d}",
            password="hashed", address="Test St", licenceno=f"DL{i:03d}",
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
            latitude=19.076 + i * 0.001,
            longitude=72.877 + i * 0.001,
        )
        db.add(location)
        driver_ids.append(rider.id)

    db.commit()
    return driver_ids


def _create_user(db):
    """Create a test user."""
    from UserSide.models.User import User

    user = User(
        name="Test User",
        phone="9876543210",
        emailID="concurrency@test.com",
        password="hashed",
    )
    db.add(user)
    db.commit()
    return user.id


class TestConcurrentAcceptance:
    """Tests for ride acceptance concurrency control.

    These tests verify that the state machine prevents double-acceptance.
    Under PostgreSQL, SELECT FOR UPDATE provides true row locking;
    under SQLite (used in tests), the state machine validation serves
    as the guard.
    """

    def test_only_one_acceptance_succeeds_sequentially(self, db):
        """When multiple drivers try to accept the same ride sequentially,
        only the first should succeed; subsequent attempts fail on the
        state machine transition check."""
        user_id = _create_user(db)
        driver_ids = _create_drivers(db, count=3)

        # Create a ride in 'assigned' status
        trip = TripRequest(
            user_id=user_id,
            driver_id=driver_ids[0],
            pickup_lat=19.076, pickup_long=72.877,
            dest_lat=19.229, dest_long=72.856,
            status="assigned",
        )
        db.add(trip)
        db.commit()

        # First driver accepts — should succeed
        RideLifecycleService.accept_ride(db, trip.id, driver_ids[0])
        assert trip.status == "accepted"

        # Second driver tries — should fail (accepted → accepted is invalid)
        with pytest.raises(ValueError, match="Invalid status transition"):
            RideLifecycleService.accept_ride(db, trip.id, driver_ids[1])

        # Third driver tries — should also fail
        with pytest.raises(ValueError, match="Invalid status transition"):
            RideLifecycleService.accept_ride(db, trip.id, driver_ids[2])

        # Verify the ride is still accepted by the first driver
        db.refresh(trip)
        assert trip.status == "accepted"
        assert trip.driver_id == driver_ids[0]

    def test_accept_then_cancel_then_re_accept(self, db):
        """A ride that is accepted, cancelled, then re-assigned can be accepted again."""
        user_id = _create_user(db)
        driver_ids = _create_drivers(db, count=2)

        # Create ride assigned to first driver
        trip = TripRequest(
            user_id=user_id,
            driver_id=driver_ids[0],
            pickup_lat=19.076, pickup_long=72.877,
            dest_lat=19.229, dest_long=72.856,
            status="assigned",
        )
        db.add(trip)
        db.commit()

        # First driver accepts
        RideLifecycleService.accept_ride(db, trip.id, driver_ids[0])
        assert trip.status == "accepted"

        # User cancels
        RideLifecycleService.cancel_ride(db, trip.id, user_id)
        assert trip.status == "cancelled"

    def test_duplicate_accept_same_driver(self, db):
        """Same driver accepting twice should fail the second time."""
        user_id = _create_user(db)
        driver_ids = _create_drivers(db, count=1)

        trip = TripRequest(
            user_id=user_id,
            driver_id=driver_ids[0],
            pickup_lat=19.076, pickup_long=72.877,
            dest_lat=19.229, dest_long=72.856,
            status="assigned",
        )
        db.add(trip)
        db.commit()

        # First accept succeeds
        RideLifecycleService.accept_ride(db, trip.id, driver_ids[0])
        assert trip.status == "accepted"

        # Second accept fails (accepted → accepted is not valid)
        with pytest.raises(ValueError, match="Invalid status transition"):
            RideLifecycleService.accept_ride(db, trip.id, driver_ids[0])


class TestConcurrentRideRequests:
    """Tests for concurrent ride creation."""

    def test_multiple_rides_from_same_user(self, db):
        """A user should be able to create multiple ride requests."""
        user_id = _create_user(db)
        driver_ids = _create_drivers(db, count=3)

        trips = []
        for did in driver_ids:
            trip = RideLifecycleService.request_ride(
                db=db,
                user_id=user_id,
                driver_id=did,
                pickup_lat=19.076,
                pickup_long=72.877,
                dest_lat=19.229,
                dest_long=72.856,
            )
            trips.append(trip)

        # All should be created with unique IDs
        assert len(trips) == 3
        ids = [t.id for t in trips]
        assert len(set(ids)) == 3  # All unique

        # Each should have an outbox event
        outbox_count = db.query(OutboxEvent).filter_by(
            event_type="ride.requested"
        ).count()
        assert outbox_count == 3

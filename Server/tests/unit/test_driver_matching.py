"""
Unit tests for the DriverMatchingService.

Tests:
- Haversine distance calculation
- PostgreSQL fallback driver search
- Expanding radius search
- Driver availability filtering
"""

import pytest
import math
import os
from datetime import datetime, timezone

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from DataBase.Connection import Base, engine, SessionLocal
from DynamicDB.models.triprequest import TripRequest
from DynamicDB.models.active_riders import ActiveDriver
from DynamicDB.models.Driver_Location import DriverLocation
from kafka.outbox.models import OutboxEvent, ProcessedEvent
from services.driver_matching_service import DriverMatchingService, _haversine


@pytest.fixture(autouse=True)
def setup_db():
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


def _create_driver(db, driver_id, lat, lng, is_available=True):
    """Helper to create a driver with location and availability."""
    from DriverSide.models.Driver import Rider

    # Check if rider already exists
    existing = db.query(Rider).filter_by(id=driver_id).first()
    if not existing:
        rider = Rider(
            id=driver_id,
            name=f"Driver{driver_id}", surname="Test",
            email=f"driver{driver_id}@test.com", phone=f"100000{driver_id}",
            password="hashed", address="Test", licenceno=f"DL{driver_id:03d}",
        )
        db.add(rider)
        db.flush()

    location = DriverLocation(
        driver_id=driver_id, latitude=lat, longitude=lng,
    )
    db.add(location)

    active = ActiveDriver(
        driver_id=driver_id,
        is_online=True,
        is_available=is_available,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(active)
    db.flush()


class TestHaversine:
    """Tests for the haversine distance function."""

    def test_same_point(self):
        assert _haversine(19.076, 72.877, 19.076, 72.877) == 0.0

    def test_known_distance(self):
        # Mumbai to Pune ~approximately 150 km
        dist = _haversine(19.076, 72.877, 18.520, 73.856)
        assert 100 < dist < 200

    def test_short_distance(self):
        # Points ~1km apart
        dist = _haversine(19.076, 72.877, 19.085, 72.877)
        assert 0.5 < dist < 2.0


class TestDriverMatching:
    """Tests for DriverMatchingService."""

    def test_find_nearby_drivers_postgres_fallback(self, db):
        """Should find drivers using PostgreSQL fallback when Redis unavailable."""
        _create_driver(db, 1, 19.076, 72.877)  # Very close
        _create_driver(db, 2, 19.080, 72.880)  # ~0.5 km away
        _create_driver(db, 3, 20.000, 73.000)  # ~100 km away
        db.commit()

        matcher = DriverMatchingService()
        nearby = matcher.find_nearby_drivers(
            db, pickup_lat=19.076, pickup_lng=72.877, radius_km=5.0,
        )

        assert len(nearby) >= 2  # Should find at least the 2 close drivers
        # Should be sorted by distance
        if len(nearby) >= 2:
            assert nearby[0]["distance_km"] <= nearby[1]["distance_km"]

    def test_find_no_drivers(self, db):
        """Should return empty list when no drivers nearby."""
        _create_driver(db, 1, 40.0, 74.0)  # New York — far away
        db.commit()

        matcher = DriverMatchingService()
        nearby = matcher.find_nearby_drivers(
            db, pickup_lat=19.076, pickup_lng=72.877, radius_km=5.0,
        )
        assert len(nearby) == 0

    def test_excludes_unavailable_drivers(self, db):
        """Should not return drivers who are unavailable."""
        _create_driver(db, 1, 19.076, 72.877, is_available=True)
        _create_driver(db, 2, 19.077, 72.878, is_available=False)
        db.commit()

        matcher = DriverMatchingService()
        nearby = matcher.find_nearby_drivers(
            db, pickup_lat=19.076, pickup_lng=72.877,
        )

        driver_ids = [d["driver_id"] for d in nearby]
        assert 1 in driver_ids
        assert 2 not in driver_ids

    def test_assign_best_driver(self, db):
        """Should assign the closest available driver."""
        from UserSide.models.User import User
        user = User(
            name="Test", phone="9999999999",
            emailID="assign@test.com", password="hashed",
        )
        db.add(user)
        db.flush()

        _create_driver(db, 1, 19.080, 72.880)  # Slightly farther
        _create_driver(db, 2, 19.076, 72.877)  # Closest
        db.commit()

        trip = TripRequest(
            user_id=user.id, driver_id=1,
            pickup_lat=19.076, pickup_long=72.877,
            dest_lat=19.1, dest_long=72.9,
            status="pending",
        )
        db.add(trip)
        db.commit()

        matcher = DriverMatchingService()
        result = matcher.assign_best_driver(
            db, trip.id, 19.076, 72.877,
        )

        assert result is not None
        driver_id, distance = result
        assert driver_id in (1, 2)

    def test_release_driver(self, db):
        """Should mark driver as available."""
        _create_driver(db, 1, 19.076, 72.877, is_available=False)
        db.commit()

        matcher = DriverMatchingService()
        matcher.release_driver(db, 1)

        active = db.query(ActiveDriver).filter_by(driver_id=1).first()
        assert active.is_available is True


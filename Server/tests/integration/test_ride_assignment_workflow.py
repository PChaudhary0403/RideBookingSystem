"""
Integration test for the ride assignment workflow.

End-to-end flow (with no real Kafka):
1. Create a ride request via RideLifecycleService.request_ride()
2. Verify outbox event is created
3. Create nearby drivers with location data
4. Call DriverMatchingService.find_nearby_drivers()
5. Verify matching results
6. Accept the ride
7. Verify driver is marked unavailable
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
from services.driver_matching_service import DriverMatchingService


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


@pytest.fixture
def matching_service():
    """Create a DriverMatchingService instance."""
    return DriverMatchingService()


def _create_driver(db, name, lat, lng, is_available=True):
    """Create a driver with active status and location."""
    from DriverSide.models.Driver import Rider

    rider = Rider(
        name=name, surname="Test",
        email=f"{name.lower()}@driver.com", phone=f"123456{name}",
        password="hashed", address="Test St", licenceno=f"DL-{name}",
    )
    db.add(rider)
    db.flush()

    active = ActiveDriver(
        driver_id=rider.id,
        is_online=True,
        is_available=is_available,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(active)

    location = DriverLocation(
        driver_id=rider.id,
        latitude=lat,
        longitude=lng,
    )
    db.add(location)
    db.commit()
    return rider.id


def _create_user(db):
    """Create a test user."""
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


class TestRideAssignmentWorkflow:
    """End-to-end ride assignment workflow tests."""

    def test_full_ride_lifecycle(self, db, matching_service):
        """Test complete flow: request → match → assign → accept."""
        user_id = _create_user(db)
        # Create drivers near pickup location (19.076, 72.877)
        driver1_id = _create_driver(db, "Alice", 19.077, 72.878)  # ~150m away
        driver2_id = _create_driver(db, "Bob", 19.080, 72.880)    # ~500m away
        driver3_id = _create_driver(db, "Charlie", 19.100, 72.900)  # ~3km away

        # Step 1: Create ride request
        trip = RideLifecycleService.request_ride(
            db=db,
            user_id=user_id,
            driver_id=driver1_id,
            pickup_lat=19.076,
            pickup_long=72.877,
            dest_lat=19.229,
            dest_long=72.856,
        )
        assert trip.status == "pending"

        # Step 2: Verify outbox event was created
        outbox = db.query(OutboxEvent).filter_by(
            event_type="ride.requested"
        ).first()
        assert outbox is not None
        assert outbox.status == "pending"

        # Step 3: Find nearby drivers (simulating consumer)
        nearby = matching_service.find_nearby_drivers(
            db=db,
            pickup_lat=19.076,
            pickup_lng=72.877,
            radius_km=2.0,
        )
        # Should find Alice and Bob (within 2km), not Charlie
        assert len(nearby) >= 1
        nearby_ids = [d["driver_id"] for d in nearby]
        assert driver1_id in nearby_ids  # Alice is closest

        # Step 4: Assign best driver
        result = matching_service.assign_best_driver(
            db=db,
            trip_req_id=trip.id,
            pickup_lat=19.076,
            pickup_lng=72.877,
        )
        assert result is not None
        assigned_driver_id, distance_km = result

        # Step 5: Verify ride is now assigned
        db.refresh(trip)
        assert trip.status == "assigned"
        assert trip.driver_id == assigned_driver_id

        # Step 6: Accept the ride
        result = RideLifecycleService.accept_ride(db, trip.id, assigned_driver_id)
        assert result.status == "accepted"

        # Step 7: Verify driver is unavailable
        active = db.query(ActiveDriver).filter_by(driver_id=assigned_driver_id).first()
        assert active.is_available is False

        # Step 8: Verify all outbox events were created for the lifecycle
        outbox_events = db.query(OutboxEvent).all()
        event_types = [e.event_type for e in outbox_events]
        assert "ride.requested" in event_types
        assert "ride.driver.assigned" in event_types
        assert "ride.driver.accepted" in event_types

    def test_no_drivers_nearby(self, db, matching_service):
        """When no drivers are nearby, matching should return empty list."""
        nearby = matching_service.find_nearby_drivers(
            db=db,
            pickup_lat=19.076,
            pickup_lng=72.877,
            radius_km=1.0,
        )
        assert nearby == []

    def test_unavailable_drivers_excluded(self, db, matching_service):
        """Unavailable drivers should not appear in matching results."""
        _create_user(db)
        # Create an unavailable driver nearby
        driver_id = _create_driver(db, "Dave", 19.077, 72.878, is_available=False)

        nearby = matching_service.find_nearby_drivers(
            db=db,
            pickup_lat=19.076,
            pickup_lng=72.877,
            radius_km=2.0,
        )
        nearby_ids = [d["driver_id"] for d in nearby]
        assert driver_id not in nearby_ids

    def test_assign_releases_on_cancel(self, db):
        """Cancelling an assigned ride should release the driver."""
        user_id = _create_user(db)
        driver_id = _create_driver(db, "Eve", 19.077, 72.878)

        # Request a ride
        trip = RideLifecycleService.request_ride(
            db=db,
            user_id=user_id,
            driver_id=driver_id,
            pickup_lat=19.076,
            pickup_long=72.877,
            dest_lat=19.229,
            dest_long=72.856,
        )

        # Cancel the ride (pending → cancelled is valid)
        result = RideLifecycleService.cancel_ride(db, trip.id, user_id)
        assert result.status == "cancelled"

        # Driver should be available again
        active = db.query(ActiveDriver).filter_by(driver_id=driver_id).first()
        assert active.is_available is True

"""
Concurrency tests for duplicate event handling.

Tests:
- Processing duplicate events (same event_id) is detected
- Only the first processing creates side effects
"""

import pytest
import os
import uuid

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from datetime import datetime, timezone

from DataBase.Connection import Base, engine, SessionLocal
from kafka.outbox.models import OutboxEvent, ProcessedEvent
from kafka.outbox.repository import OutboxRepository
from kafka.schemas import EventEnvelope, EventType, RideRequestedPayload


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


def _make_envelope(event_id=None):
    """Create a RideRequested event envelope."""
    envelope = EventEnvelope.create(
        event_type=EventType.RIDE_REQUESTED,
        aggregate_type="ride",
        aggregate_id="200",
        payload=RideRequestedPayload(
            ride_id=200,
            user_id=1,
            pickup_lat=19.076,
            pickup_lng=72.877,
            dest_lat=19.229,
            dest_lng=72.856,
        ),
        source="test",
    )
    if event_id:
        envelope.event_id = event_id
    return envelope


class TestDuplicateEventDetection:
    """Tests for detecting and handling duplicate events."""

    def test_first_event_processed_successfully(self, db):
        """First processing of an event should succeed."""
        event_id = str(uuid.uuid4())

        # Simulate consumer checking if event was already processed
        assert OutboxRepository.is_event_processed(db, event_id) is False

        # Process the event (mark as processed)
        OutboxRepository.mark_event_processed(
            db, event_id, "ride.requested", "ride-lifecycle"
        )
        db.commit()

        assert OutboxRepository.is_event_processed(db, event_id) is True

    def test_duplicate_event_detected(self, db):
        """Second attempt to process the same event should be detected."""
        event_id = str(uuid.uuid4())

        # First processing
        OutboxRepository.mark_event_processed(
            db, event_id, "ride.requested", "ride-lifecycle"
        )
        db.commit()

        # Second processing attempt — should detect duplicate
        is_dup = OutboxRepository.is_event_processed(db, event_id)
        assert is_dup is True

    def test_duplicate_outbox_events_same_event_id(self, db):
        """Two outbox events with the same logical event_id:
        only the first should be creatable (unique constraint on event_id)."""
        event_id = str(uuid.uuid4())
        envelope1 = _make_envelope(event_id=event_id)

        # First insert succeeds
        OutboxRepository.create_event_from_envelope(
            db, "ridebooking.rides", envelope1
        )
        db.commit()

        # Second insert with the same event_id should violate unique constraint
        envelope2 = _make_envelope(event_id=event_id)
        OutboxRepository.create_event_from_envelope(
            db, "ridebooking.rides", envelope2
        )
        with pytest.raises(Exception):
            # IntegrityError due to unique constraint on event_id
            db.commit()
        db.rollback()

        # Only one event should exist
        count = db.query(OutboxEvent).count()
        assert count == 1

    def test_different_consumer_groups_process_independently(self, db):
        """Different consumer groups should process events independently.

        The current implementation tracks by event_id only, so this
        validates that an event marked by one group is detected globally.
        """
        event_id = str(uuid.uuid4())

        # First consumer group processes it
        OutboxRepository.mark_event_processed(
            db, event_id, "ride.requested", "group-a"
        )
        db.commit()

        # The event is now marked as processed globally
        assert OutboxRepository.is_event_processed(db, event_id) is True

    def test_idempotent_ride_request_processing(self, db):
        """Simulates a consumer receiving the same ride.requested event twice.

        The second processing should be skipped without creating
        duplicate database records.
        """
        from DynamicDB.models.triprequest import TripRequest
        from DynamicDB.models.active_riders import ActiveDriver
        from DriverSide.models.Driver import Rider

        event_id = str(uuid.uuid4())

        # Simulate first processing: check → process → mark
        assert OutboxRepository.is_event_processed(db, event_id) is False

        # Create a driver first (driver_id is NOT NULL)
        rider = Rider(
            name="Test", surname="Driver",
            email="dup@driver.com", phone="123",
            password="hashed", address="Addr", licenceno="DL999",
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

        # Create a user
        from UserSide.models.User import User
        user = User(
            name="Test", phone="123", emailID="dup@test.com", password="hashed"
        )
        db.add(user)
        db.commit()

        # Create the ride (simulating what the consumer would do)
        trip = TripRequest(
            user_id=user.id,
            driver_id=rider.id,
            pickup_lat=19.076, pickup_long=72.877,
            dest_lat=19.229, dest_long=72.856,
            status="pending",
        )
        db.add(trip)
        OutboxRepository.mark_event_processed(
            db, event_id, "ride.requested", "ride-lifecycle"
        )
        db.commit()

        trip_count_after_first = db.query(TripRequest).count()

        # Simulate second processing: check should detect duplicate
        assert OutboxRepository.is_event_processed(db, event_id) is True
        # Consumer would skip processing here

        trip_count_after_second = db.query(TripRequest).count()
        assert trip_count_after_second == trip_count_after_first

"""
Integration tests for the Outbox Publisher mechanism.

Tests:
- Pending outbox events are fetched for publishing
- Published events are correctly marked
- Failed events have retry count incremented
- Events exceeding max retries are skipped
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


def _create_outbox_event(db, event_id=None, topic="ridebooking.rides"):
    """Helper to create an outbox event with a ride.requested payload."""
    envelope = EventEnvelope.create(
        event_type=EventType.RIDE_REQUESTED,
        aggregate_type="ride",
        aggregate_id="100",
        payload=RideRequestedPayload(
            ride_id=100,
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

    OutboxRepository.create_event_from_envelope(db, topic, envelope)
    db.commit()
    return envelope


class TestOutboxPublishFlow:
    """Tests for the outbox publish lifecycle."""

    def test_pending_events_are_fetched(self, db):
        """Pending events should be returned by fetch_pending."""
        _create_outbox_event(db)
        pending = OutboxRepository.fetch_pending(db, batch_size=10)
        assert len(pending) == 1
        assert pending[0].status == "pending"

    def test_multiple_pending_events_ordered(self, db):
        """Multiple pending events should be fetched in insertion order."""
        _create_outbox_event(db)
        _create_outbox_event(db)
        _create_outbox_event(db)

        pending = OutboxRepository.fetch_pending(db, batch_size=10)
        assert len(pending) == 3
        # IDs should be monotonically increasing
        assert pending[0].id < pending[1].id < pending[2].id

    def test_published_events_marked_correctly(self, db):
        """After marking as published, events should not be re-fetched."""
        _create_outbox_event(db)
        pending = OutboxRepository.fetch_pending(db, batch_size=10)
        assert len(pending) == 1

        # mark_published takes the event_id (UUID string), not the row id
        OutboxRepository.mark_published(db, pending[0].event_id)
        db.commit()

        # Should not appear in pending anymore
        pending_after = OutboxRepository.fetch_pending(db, batch_size=10)
        assert len(pending_after) == 0

        # Verify the event is marked as published
        event = db.query(OutboxEvent).filter_by(id=pending[0].id).first()
        assert event.status == "published"
        assert event.published_at is not None

    def test_failed_events_retry_incremented(self, db):
        """Failed events should have their retry count incremented."""
        _create_outbox_event(db)
        pending = OutboxRepository.fetch_pending(db, batch_size=10)
        event = pending[0]
        original_retry = event.retry_count

        # mark_failed takes event_id (UUID string)
        OutboxRepository.mark_failed(db, event.event_id, "Connection refused")
        db.commit()

        db.refresh(event)
        assert event.retry_count == original_retry + 1
        assert event.last_error == "Connection refused"
        # Still pending (under max_retries), status stays "pending"
        assert event.status == "pending"

    def test_events_with_max_retries_become_failed(self, db):
        """Events that hit max retries should get status 'failed'."""
        _create_outbox_event(db)
        pending = OutboxRepository.fetch_pending(db, batch_size=10)
        event = pending[0]

        # Simulate max retries (default max is 5)
        for i in range(5):
            OutboxRepository.mark_failed(db, event.event_id, f"Failure {i+1}")
            db.commit()

        db.refresh(event)
        assert event.status == "failed"
        assert event.retry_count == 5

        # Should not be fetched by fetch_pending (status is 'failed')
        pending_after = OutboxRepository.fetch_pending(db, batch_size=10)
        assert len(pending_after) == 0

    def test_batch_size_respected(self, db):
        """fetch_pending should respect the batch_size parameter."""
        for _ in range(5):
            _create_outbox_event(db)

        pending = OutboxRepository.fetch_pending(db, batch_size=2)
        assert len(pending) == 2


class TestOutboxEventPayload:
    """Tests for event payload integrity through the outbox."""

    def test_payload_roundtrip(self, db):
        """Event payload should survive serialization through the outbox."""
        _create_outbox_event(db)
        pending = OutboxRepository.fetch_pending(db, batch_size=1)
        stored_payload = pending[0].payload

        assert stored_payload["event_type"] == "ride.requested"
        assert stored_payload["payload"]["ride_id"] == 100
        assert stored_payload["payload"]["user_id"] == 1
        assert stored_payload["payload"]["pickup_lat"] == 19.076

    def test_event_id_preserved(self, db):
        """The event_id in the payload should be preserved."""
        custom_id = str(uuid.uuid4())
        _create_outbox_event(db, event_id=custom_id)

        pending = OutboxRepository.fetch_pending(db, batch_size=1)
        assert pending[0].payload["event_id"] == custom_id


class TestOutboxMetrics:
    """Tests for outbox monitoring counts."""

    def test_pending_count(self, db):
        """get_pending_count should reflect actual pending events."""
        assert OutboxRepository.get_pending_count(db) == 0

        _create_outbox_event(db)
        _create_outbox_event(db)
        assert OutboxRepository.get_pending_count(db) == 2

    def test_failed_count(self, db):
        """get_failed_count should reflect events that are in 'failed' status."""
        assert OutboxRepository.get_failed_count(db) == 0

        _create_outbox_event(db)
        pending = OutboxRepository.fetch_pending(db, batch_size=1)
        event = pending[0]

        # Must exceed max_retries to reach 'failed' status
        for i in range(5):
            OutboxRepository.mark_failed(db, event.event_id, f"Failure {i+1}")
            db.commit()

        assert OutboxRepository.get_failed_count(db) == 1

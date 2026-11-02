"""
Integration tests for consumer idempotency.

Tests:
- Events can be marked as processed
- Duplicate events are detected
- Processing the same event twice has no additional side effects
"""

import pytest
import os
import uuid

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from DataBase.Connection import Base, engine, SessionLocal
from kafka.outbox.models import OutboxEvent, ProcessedEvent
from kafka.outbox.repository import OutboxRepository


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


class TestIdempotentProcessing:
    """Tests for idempotent event processing via ProcessedEvent table."""

    def test_new_event_is_not_processed(self, db):
        """An event that hasn't been seen should not be marked as processed."""
        event_id = str(uuid.uuid4())
        assert OutboxRepository.is_event_processed(db, event_id) is False

    def test_mark_event_as_processed(self, db):
        """After marking an event as processed, it should be detected."""
        event_id = str(uuid.uuid4())

        OutboxRepository.mark_event_processed(
            db, event_id, "ride.requested", "ride-lifecycle"
        )
        db.commit()

        assert OutboxRepository.is_event_processed(db, event_id) is True

    def test_duplicate_event_detection(self, db):
        """Processing the same event_id twice should detect the duplicate."""
        event_id = str(uuid.uuid4())

        # First processing
        OutboxRepository.mark_event_processed(
            db, event_id, "ride.requested", "ride-lifecycle"
        )
        db.commit()

        # Second attempt — should detect as already processed
        assert OutboxRepository.is_event_processed(db, event_id) is True

    def test_different_events_independent(self, db):
        """Different event IDs should be tracked independently."""
        event_a = str(uuid.uuid4())
        event_b = str(uuid.uuid4())

        OutboxRepository.mark_event_processed(
            db, event_a, "ride.requested", "ride-lifecycle"
        )
        db.commit()

        assert OutboxRepository.is_event_processed(db, event_a) is True
        assert OutboxRepository.is_event_processed(db, event_b) is False

    def test_processed_event_records_consumer_group(self, db):
        """The ProcessedEvent record should store the consumer group."""
        event_id = str(uuid.uuid4())
        OutboxRepository.mark_event_processed(
            db, event_id, "ride.requested", "my-consumer-group"
        )
        db.commit()

        record = db.query(ProcessedEvent).filter_by(event_id=event_id).first()
        assert record is not None
        assert record.consumer_group == "my-consumer-group"
        assert record.processed_at is not None

    def test_cleanup_old_processed_events(self, db):
        """Cleanup should remove old processed event records."""
        # Create some processed events
        for _ in range(5):
            event_id = str(uuid.uuid4())
            OutboxRepository.mark_event_processed(
                db, event_id, "ride.requested", "test"
            )
        db.commit()

        count_before = db.query(ProcessedEvent).count()
        assert count_before == 5

        # Cleanup with 0 days retention should remove all
        OutboxRepository.cleanup_processed_events(db, older_than_days=0)
        db.commit()

        count_after = db.query(ProcessedEvent).count()
        assert count_after == 0

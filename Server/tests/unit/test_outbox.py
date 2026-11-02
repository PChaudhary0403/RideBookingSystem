"""
Unit tests for the Transactional Outbox pattern.

Tests:
- OutboxEvent model creation
- ProcessedEvent deduplication
- OutboxRepository CRUD operations
- Event lifecycle: pending → published / failed
- Cleanup operations
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

# Set env vars before importing app modules
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from DataBase.Connection import Base, engine, SessionLocal
from kafka.outbox.models import OutboxEvent, ProcessedEvent
from kafka.outbox.repository import OutboxRepository


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Provide a clean DB session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── OutboxEvent model tests ───────────────────────────────────────────────

class TestOutboxEventModel:
    """Tests for OutboxEvent SQLAlchemy model."""

    def test_create_outbox_event(self, db):
        event = OutboxEvent(
            event_id="test-uuid-123",
            event_type="ride.requested",
            aggregate_type="ride",
            aggregate_id="42",
            topic="ridebooking.rides.v1",
            payload={"ride_id": 42, "user_id": 7},
            status="pending",
        )
        db.add(event)
        db.commit()

        fetched = db.query(OutboxEvent).filter_by(event_id="test-uuid-123").first()
        assert fetched is not None
        assert fetched.event_type == "ride.requested"
        assert fetched.aggregate_id == "42"
        assert fetched.status == "pending"
        assert fetched.retry_count == 0

    def test_default_values(self, db):
        event = OutboxEvent(
            event_type="test.event",
            aggregate_type="test",
            aggregate_id="1",
            topic="test.topic",
            payload={},
        )
        db.add(event)
        db.commit()

        assert event.event_id is not None
        assert len(event.event_id) == 36
        assert event.status == "pending"
        assert event.retry_count == 0
        assert event.max_retries == 5


# ── OutboxRepository tests ────────────────────────────────────────────────

class TestOutboxRepository:
    """Tests for OutboxRepository operations."""

    def test_add_event(self, db):
        event = OutboxRepository.add_event(
            db=db,
            event_type="ride.requested",
            aggregate_type="ride",
            aggregate_id="10",
            topic="ridebooking.rides.v1",
            payload={"ride_id": 10},
        )
        db.commit()

        assert event.event_id is not None
        assert event.status == "pending"

    def test_fetch_pending(self, db):
        # Insert 3 pending events
        for i in range(3):
            OutboxRepository.add_event(
                db=db,
                event_type="ride.requested",
                aggregate_type="ride",
                aggregate_id=str(i),
                topic="ridebooking.rides.v1",
                payload={"ride_id": i},
            )
        db.commit()

        # Use skip_locked=False for SQLite
        pending = OutboxRepository.fetch_pending(db, batch_size=10, use_skip_locked=False)
        assert len(pending) == 3

    def test_fetch_pending_respects_batch_size(self, db):
        for i in range(5):
            OutboxRepository.add_event(
                db=db,
                event_type="test",
                aggregate_type="test",
                aggregate_id=str(i),
                topic="test",
                payload={},
            )
        db.commit()

        pending = OutboxRepository.fetch_pending(db, batch_size=2, use_skip_locked=False)
        assert len(pending) == 2

    def test_mark_published(self, db):
        event = OutboxRepository.add_event(
            db=db,
            event_type="test",
            aggregate_type="test",
            aggregate_id="1",
            topic="test",
            payload={},
        )
        db.commit()

        OutboxRepository.mark_published(db, event.event_id)
        db.commit()

        fetched = db.query(OutboxEvent).filter_by(event_id=event.event_id).first()
        assert fetched.status == "published"
        assert fetched.published_at is not None

    def test_mark_failed_increments_retry(self, db):
        event = OutboxRepository.add_event(
            db=db,
            event_type="test",
            aggregate_type="test",
            aggregate_id="1",
            topic="test",
            payload={},
            max_retries=3,
        )
        db.commit()

        # First failure — should stay pending
        OutboxRepository.mark_failed(db, event.event_id, "connection error")
        db.commit()
        db.refresh(event)
        assert event.retry_count == 1
        assert event.status == "pending"

        # Second failure
        OutboxRepository.mark_failed(db, event.event_id, "timeout")
        db.commit()
        db.refresh(event)
        assert event.retry_count == 2

        # Third failure — should be marked failed (exhausted)
        OutboxRepository.mark_failed(db, event.event_id, "broker down")
        db.commit()
        db.refresh(event)
        assert event.retry_count == 3
        assert event.status == "failed"

    def test_published_events_not_refetched(self, db):
        event = OutboxRepository.add_event(
            db=db,
            event_type="test",
            aggregate_type="test",
            aggregate_id="1",
            topic="test",
            payload={},
        )
        db.commit()

        OutboxRepository.mark_published(db, event.event_id)
        db.commit()

        pending = OutboxRepository.fetch_pending(db, use_skip_locked=False)
        assert len(pending) == 0

    def test_get_pending_count(self, db):
        for i in range(4):
            OutboxRepository.add_event(
                db=db,
                event_type="test",
                aggregate_type="test",
                aggregate_id=str(i),
                topic="test",
                payload={},
            )
        db.commit()

        assert OutboxRepository.get_pending_count(db) == 4

    def test_get_failed_count(self, db):
        event = OutboxRepository.add_event(
            db=db,
            event_type="test",
            aggregate_type="test",
            aggregate_id="1",
            topic="test",
            payload={},
            max_retries=1,
        )
        db.commit()

        OutboxRepository.mark_failed(db, event.event_id, "error")
        db.commit()

        assert OutboxRepository.get_failed_count(db) == 1


# ── Idempotency (ProcessedEvent) tests ────────────────────────────────────

class TestIdempotency:
    """Tests for consumer idempotency via ProcessedEvent."""

    def test_is_event_processed_false(self, db):
        assert OutboxRepository.is_event_processed(db, "nonexistent-id") is False

    def test_mark_and_check_processed(self, db):
        OutboxRepository.mark_event_processed(
            db, "event-123", "ride.requested", "test-consumer",
        )
        db.commit()

        assert OutboxRepository.is_event_processed(db, "event-123") is True
        assert OutboxRepository.is_event_processed(db, "event-456") is False

    def test_duplicate_event_detected(self, db):
        OutboxRepository.mark_event_processed(db, "dup-1", "test", "group")
        db.commit()

        # Simulating consumer check before processing
        is_dup = OutboxRepository.is_event_processed(db, "dup-1")
        assert is_dup is True


# ── Cleanup tests ─────────────────────────────────────────────────────────

class TestCleanup:
    """Tests for maintenance cleanup operations."""

    def test_cleanup_published(self, db):
        event = OutboxRepository.add_event(
            db=db,
            event_type="test",
            aggregate_type="test",
            aggregate_id="1",
            topic="test",
            payload={},
        )
        db.commit()

        # Manually set published_at to 48 hours ago
        event.status = "published"
        event.published_at = datetime.now(timezone.utc) - timedelta(hours=48)
        db.commit()

        deleted = OutboxRepository.cleanup_published(db, older_than_hours=24)
        db.commit()
        assert deleted == 1

    def test_cleanup_processed_events(self, db):
        record = ProcessedEvent(
            event_id="old-event",
            event_type="test",
            consumer_group="test",
            processed_at=datetime.now(timezone.utc) - timedelta(days=10),
        )
        db.add(record)
        db.commit()

        deleted = OutboxRepository.cleanup_processed_events(db, older_than_days=7)
        db.commit()
        assert deleted == 1


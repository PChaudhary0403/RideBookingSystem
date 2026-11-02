"""
Database operations for the Transactional Outbox.

Provides ``OutboxRepository`` for:
- Atomically inserting outbox events alongside business state changes
- Fetching pending events for the background publisher
- Marking events as published or failed
- Checking for duplicate events (idempotent consumers)
- Cleanup of old published/processed events
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, text
from sqlalchemy.orm import Session

from kafka.outbox.models import OutboxEvent, ProcessedEvent
from kafka.schemas import EventEnvelope

logger = logging.getLogger(__name__)


class OutboxRepository:
    """Repository for outbox and processed-event operations.

    All methods accept an explicit ``db`` session so callers can
    include outbox writes in the same transaction as business state
    changes.  The caller is responsible for committing the transaction.
    """

    @staticmethod
    def add_event(
        db: Session,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        topic: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        max_retries: int = 5,
    ) -> OutboxEvent:
        """Insert a new outbox event.

        This must be called inside the same DB transaction as the
        corresponding business state change.

        Args:
            db: Active SQLAlchemy session (caller manages the transaction).
            event_type: Event type string (e.g. ``ride.requested``).
            aggregate_type: Entity type (``ride``, ``driver``).
            aggregate_id: Partition key value.
            topic: Target Kafka topic name.
            payload: Full event envelope dict (serialized EventEnvelope).
            event_id: Optional UUID; generated if not provided.
            max_retries: Maximum publish attempts before ``failed``.

        Returns:
            The created OutboxEvent instance (not yet committed).
        """
        event = OutboxEvent(
            event_id=event_id or str(uuid.uuid4()),
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            topic=topic,
            payload=payload,
            max_retries=max_retries,
            status="pending",
        )
        db.add(event)
        logger.debug(
            "Outbox event queued: type=%s aggregate=%s:%s",
            event_type,
            aggregate_type,
            aggregate_id,
        )
        return event

    @staticmethod
    def create_event_from_envelope(
        db: Session,
        topic: str,
        envelope: EventEnvelope,
        max_retries: int = 5,
    ) -> OutboxEvent:
        """Convenience method to insert an outbox event from an EventEnvelope.

        Args:
            db: Active SQLAlchemy session.
            topic: Target Kafka topic name.
            envelope: A pre-built EventEnvelope.
            max_retries: Maximum publish attempts.

        Returns:
            The created OutboxEvent instance.
        """
        return OutboxRepository.add_event(
            db=db,
            event_type=envelope.event_type,
            aggregate_type=envelope.aggregate_type,
            aggregate_id=envelope.aggregate_id,
            topic=topic,
            payload=envelope.model_dump(mode="json"),
            event_id=envelope.event_id,
            max_retries=max_retries,
        )

    @staticmethod
    def fetch_pending(
        db: Session,
        batch_size: int = 50,
        use_skip_locked: bool = True,
    ) -> List[OutboxEvent]:
        """Fetch pending outbox events for publishing.

        Uses ``SELECT ... FOR UPDATE SKIP LOCKED`` when available
        (PostgreSQL) to allow multiple publishers to run concurrently
        without conflicts.

        Args:
            db: Active SQLAlchemy session.
            batch_size: Maximum number of events to fetch.
            use_skip_locked: Whether to use SKIP LOCKED (disable for SQLite).

        Returns:
            A list of pending OutboxEvent instances.
        """
        query = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at.asc())
            .limit(batch_size)
        )

        if use_skip_locked:
            try:
                query = query.with_for_update(skip_locked=True)
            except Exception:
                # SQLite doesn't support FOR UPDATE; fall through
                pass

        return query.all()

    @staticmethod
    def fetch_retryable(
        db: Session,
        batch_size: int = 20,
    ) -> List[OutboxEvent]:
        """Fetch failed events that are eligible for retry.

        Args:
            db: Active SQLAlchemy session.
            batch_size: Maximum number of events to fetch.

        Returns:
            A list of retryable OutboxEvent instances.
        """
        return (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.status == "failed",
                OutboxEvent.retry_count < OutboxEvent.max_retries,
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(batch_size)
            .all()
        )

    @staticmethod
    def mark_published(
        db: Session,
        event_id: str,
    ) -> None:
        """Mark an outbox event as successfully published.

        Args:
            db: Active SQLAlchemy session.
            event_id: The UUID of the event to mark.
        """
        event = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.event_id == event_id)
            .first()
        )
        if event:
            event.status = "published"
            event.published_at = datetime.now(timezone.utc)
            logger.debug("Outbox event published: %s", event_id)

    @staticmethod
    def mark_failed(
        db: Session,
        event_id: str,
        error_message: str,
    ) -> None:
        """Increment the retry count and record the error.

        If ``retry_count >= max_retries``, the status is set to ``failed``.

        Args:
            db: Active SQLAlchemy session.
            event_id: The UUID of the event.
            error_message: The error description.
        """
        event = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.event_id == event_id)
            .first()
        )
        if event:
            event.retry_count += 1
            event.last_error = error_message
            if event.retry_count >= event.max_retries:
                event.status = "failed"
                logger.error(
                    "Outbox event exhausted retries: id=%s type=%s error=%s",
                    event_id,
                    event.event_type,
                    error_message,
                )
            else:
                # Keep as pending for the next polling cycle
                event.status = "pending"
                logger.warning(
                    "Outbox event publish failed (attempt %d/%d): id=%s error=%s",
                    event.retry_count,
                    event.max_retries,
                    event_id,
                    error_message,
                )

    # ── Idempotent consumer deduplication ──────────────────────────────────

    @staticmethod
    def is_event_processed(
        db: Session,
        event_id: str,
    ) -> bool:
        """Check if an event has already been processed.

        Args:
            db: Active SQLAlchemy session.
            event_id: The event UUID to check.

        Returns:
            True if the event has been processed, False otherwise.
        """
        return (
            db.query(ProcessedEvent)
            .filter(ProcessedEvent.event_id == event_id)
            .first()
        ) is not None

    @staticmethod
    def mark_event_processed(
        db: Session,
        event_id: str,
        event_type: str,
        consumer_group: str = "",
    ) -> ProcessedEvent:
        """Record that an event has been processed.

        Must be called in the same transaction as the business logic
        to guarantee atomicity.

        Args:
            db: Active SQLAlchemy session.
            event_id: The event UUID.
            event_type: The event type.
            consumer_group: The consumer group that processed it.

        Returns:
            The created ProcessedEvent instance.
        """
        record = ProcessedEvent(
            event_id=event_id,
            event_type=event_type,
            consumer_group=consumer_group,
        )
        db.add(record)
        return record

    # ── Maintenance ────────────────────────────────────────────────────────

    @staticmethod
    def cleanup_published(
        db: Session,
        older_than_hours: int = 24,
    ) -> int:
        """Delete published outbox events older than the given threshold.

        Args:
            db: Active SQLAlchemy session.
            older_than_hours: Age threshold in hours.

        Returns:
            Number of deleted rows.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        count = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.status == "published",
                OutboxEvent.published_at < cutoff,
            )
            .delete(synchronize_session=False)
        )
        if count > 0:
            logger.info("Cleaned up %d published outbox events.", count)
        return count

    @staticmethod
    def cleanup_processed_events(
        db: Session,
        older_than_days: int = 7,
    ) -> int:
        """Delete processed event records older than the given threshold.

        Args:
            db: Active SQLAlchemy session.
            older_than_days: Age threshold in days.

        Returns:
            Number of deleted rows.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        count = (
            db.query(ProcessedEvent)
            .filter(ProcessedEvent.processed_at < cutoff)
            .delete(synchronize_session=False)
        )
        if count > 0:
            logger.info("Cleaned up %d processed event records.", count)
        return count

    @staticmethod
    def get_pending_count(db: Session) -> int:
        """Return the number of pending outbox events.

        Useful for monitoring and health checks.
        """
        return (
            db.query(OutboxEvent)
            .filter(OutboxEvent.status == "pending")
            .count()
        )

    @staticmethod
    def get_failed_count(db: Session) -> int:
        """Return the number of failed outbox events."""
        return (
            db.query(OutboxEvent)
            .filter(OutboxEvent.status == "failed")
            .count()
        )

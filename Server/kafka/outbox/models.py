"""
SQLAlchemy models for the Transactional Outbox pattern.

Two tables:
- ``outbox_events``:  Events waiting to be published to Kafka.
  Written atomically with business state changes in the same DB transaction.
- ``processed_events``:  Deduplication log for idempotent consumers.
  Checked before processing to prevent duplicate side effects.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import JSON

from DataBase.Connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class OutboxEvent(Base):
    """Transactional outbox event awaiting Kafka publication.

    Business logic inserts rows into this table in the same DB transaction
    as the corresponding state change.  A background publisher polls for
    ``status='pending'`` rows and publishes them to Kafka.

    Columns:
        id:              Auto-incrementing primary key (ordering guarantee).
        event_id:        UUID for global deduplication.
        event_type:      Discriminator (e.g. ``ride.requested``).
        aggregate_type:  Entity type (``ride``, ``driver``, etc.).
        aggregate_id:    Partition key value (ride_id, driver_id as string).
        topic:           Target Kafka topic.
        payload:         Full event envelope as JSON.
        created_at:      When the event was created.
        published_at:    When the event was successfully published (nullable).
        retry_count:     Number of failed publish attempts.
        max_retries:     Maximum publish attempts before marking ``failed``.
        last_error:      Last error message from a failed publish attempt.
        status:          ``pending`` | ``published`` | ``failed``.
    """

    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), nullable=False, unique=True, default=_new_uuid)
    event_type = Column(String(100), nullable=False)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String(100), nullable=False)
    topic = Column(String(200), nullable=False)
    payload = Column(JSON, nullable=False)      # JSONB on PostgreSQL, JSON on SQLite
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    published_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=5)
    last_error = Column(Text, nullable=True)
    status = Column(
        String(20), nullable=False, default="pending",
    )

    __table_args__ = (
        Index(
            "idx_outbox_pending",
            "status", "created_at",
        ),
        Index(
            "idx_outbox_failed",
            "status", "retry_count",
        ),
        CheckConstraint(
            "status IN ('pending', 'published', 'failed')",
            name="ck_outbox_status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OutboxEvent(id={self.id}, event_type={self.event_type!r}, "
            f"aggregate_id={self.aggregate_id!r}, status={self.status!r})>"
        )


class ProcessedEvent(Base):
    """Deduplication log for idempotent event consumers.

    Before processing an event, consumers check this table for the
    ``event_id``.  If found, the event is a duplicate and is skipped.
    After successful processing, the event_id is inserted in the same
    DB transaction as the business state change.

    Columns:
        event_id:      UUID of the processed event (primary key).
        event_type:    Event type for observability.
        consumer_group: Which consumer processed this event.
        processed_at:  When the event was processed.
    """

    __tablename__ = "processed_events"

    event_id = Column(String(36), primary_key=True)
    event_type = Column(String(100), nullable=False)
    consumer_group = Column(String(100), nullable=False, default="")
    processed_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    __table_args__ = (
        Index(
            "idx_processed_events_cleanup",
            "processed_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessedEvent(event_id={self.event_id!r}, "
            f"event_type={self.event_type!r})>"
        )

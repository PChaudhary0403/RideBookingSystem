"""
Background Outbox Publisher.

Polls the ``outbox_events`` table for pending events and publishes them
to Kafka.  Runs as an asyncio background task inside the FastAPI process.

Design:
- Polls every ``outbox_poll_interval_seconds`` (default 500ms).
- Fetches up to ``outbox_batch_size`` pending events per cycle.
- Uses ``SELECT ... FOR UPDATE SKIP LOCKED`` for multi-publisher safety.
- On successful Kafka delivery: marks event as ``published``.
- On failure: increments ``retry_count``; marks ``failed`` after max retries.
- Also periodically retries failed events and cleans up old published events.

Usage::

    from kafka.outbox.publisher import OutboxPublisher

    publisher = OutboxPublisher()
    # In FastAPI lifespan:
    await publisher.start()
    # On shutdown:
    await publisher.stop()
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from DataBase.Connection import SessionLocal
from kafka.config import KafkaConfig, get_kafka_config
from kafka.outbox.repository import OutboxRepository
from kafka.producer import get_producer
from kafka.schemas import EventEnvelope

logger = logging.getLogger(__name__)


class OutboxPublisher:
    """Background task that polls outbox_events and publishes to Kafka.

    Lifecycle:
    1. ``start()`` — begins the asyncio polling loop.
    2. ``stop()`` — signals the loop to exit gracefully.

    The publisher is designed to run as a single instance per process.
    Multi-instance safety is achieved via ``SKIP LOCKED`` in the DB query.
    """

    def __init__(self, config: KafkaConfig | None = None) -> None:
        self._config = config or get_kafka_config()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._poll_interval = self._config.outbox_poll_interval_seconds
        self._batch_size = self._config.outbox_batch_size

        # Counters for monitoring
        self.total_published: int = 0
        self.total_failed: int = 0
        self._cleanup_counter: int = 0  # runs cleanup every N cycles

    async def start(self) -> None:
        """Start the background polling task."""
        if self._running:
            logger.warning("OutboxPublisher is already running.")
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            "OutboxPublisher started (interval=%.1fs, batch_size=%d).",
            self._poll_interval,
            self._batch_size,
        )

    async def stop(self) -> None:
        """Stop the polling task gracefully."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(
            "OutboxPublisher stopped. Published=%d, Failed=%d.",
            self.total_published,
            self.total_failed,
        )

    async def _poll_loop(self) -> None:
        """Main polling loop: fetch pending events, publish, repeat."""
        while self._running:
            try:
                published = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._publish_batch,
                )

                # Every 120 cycles (~60s at 500ms interval), run maintenance
                self._cleanup_counter += 1
                if self._cleanup_counter >= 120:
                    self._cleanup_counter = 0
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        self._run_maintenance,
                    )

            except Exception as exc:
                logger.error("OutboxPublisher error: %s", exc, exc_info=True)

            await asyncio.sleep(self._poll_interval)

    def _publish_batch(self) -> int:
        """Fetch and publish a batch of pending outbox events.

        Returns:
            Number of events successfully published in this batch.
        """
        db = SessionLocal()
        published_count = 0

        try:
            # Detect database type for SKIP LOCKED support
            is_sqlite = str(db.bind.url).startswith("sqlite")
            events = OutboxRepository.fetch_pending(
                db,
                batch_size=self._batch_size,
                use_skip_locked=not is_sqlite,
            )

            if not events:
                return 0

            producer = get_producer()

            for event in events:
                try:
                    # Reconstruct envelope from stored payload
                    envelope = EventEnvelope.model_validate(event.payload)

                    # Publish to Kafka
                    producer.publish(
                        topic=event.topic,
                        key=event.aggregate_id,
                        event=envelope,
                    )

                    # Mark as published
                    OutboxRepository.mark_published(db, event.event_id)
                    published_count += 1
                    self.total_published += 1

                except Exception as exc:
                    OutboxRepository.mark_failed(
                        db, event.event_id, str(exc),
                    )
                    self.total_failed += 1

            db.commit()

            # Flush producer to ensure delivery
            if published_count > 0:
                producer.flush(timeout=5)
                logger.info(
                    "Outbox batch published: %d events.", published_count,
                )

        except Exception as exc:
            db.rollback()
            logger.error("Outbox batch failed: %s", exc, exc_info=True)
        finally:
            db.close()

        return published_count

    def _run_maintenance(self) -> None:
        """Periodic maintenance: retry failed events, cleanup old ones."""
        db = SessionLocal()
        try:
            # Retry failed events that haven't exceeded max_retries
            retryable = OutboxRepository.fetch_retryable(db, batch_size=20)
            for event in retryable:
                # Reset to pending so the next poll cycle picks them up
                event.status = "pending"

            if retryable:
                db.commit()
                logger.info(
                    "Reset %d failed outbox events for retry.",
                    len(retryable),
                )

            # Clean up old published events (older than 24 hours)
            OutboxRepository.cleanup_published(db, older_than_hours=24)
            db.commit()

            # Clean up old processed_events (older than 7 days)
            OutboxRepository.cleanup_processed_events(db, older_than_days=7)
            db.commit()

        except Exception as exc:
            db.rollback()
            logger.error("Outbox maintenance failed: %s", exc)
        finally:
            db.close()

    @property
    def is_running(self) -> bool:
        """Whether the publisher loop is active."""
        return self._running

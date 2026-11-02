"""
Driver location and availability consumer.

Processes driver events from the ``ridebooking.drivers.v1`` topic:
- ``driver.location.updated``     — updates Redis geo index + PostgreSQL
- ``driver.availability.updated`` — updates driver online/available status

Location updates are HIGH FREQUENCY — idempotency checking is skipped
for them to avoid excessive ``processed_events`` table growth.  Only
availability updates are deduplicated.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Set

from DataBase.Connection import SessionLocal
from DynamicDB.models.active_riders import ActiveDriver
from DynamicDB.models.Driver_Location import DriverLocation
from kafka.consumer import BaseKafkaConsumer
from kafka.outbox.repository import OutboxRepository
from kafka.redis_client import RedisGeo
from kafka.schemas import (
    DriverAvailabilityPayload,
    DriverLocationPayload,
    EventEnvelope,
    EventType,
)
from kafka.topics import Topics

logger = logging.getLogger(__name__)


class DriverLocationConsumer(BaseKafkaConsumer):
    """Processes driver location and availability events.

    Consumer group: ``ridebooking-driver-location``

    Location updates are written to:
    1. Redis geospatial index (for O(log N) proximity queries)
    2. PostgreSQL ``driver_locations`` table (durable record)

    Availability updates are written to:
    1. PostgreSQL ``active_drivers`` table
    2. Redis geo index (remove on offline)
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            group_id="ridebooking-driver-location",
            topics=[Topics.DRIVERS],
            **kwargs,
        )
        self._geo: Optional[RedisGeo] = None

    def on_startup(self) -> None:
        """Initialize Redis geo client on consumer startup."""
        try:
            self._geo = RedisGeo()
            logger.info("Redis geo client initialized for driver consumer.")
        except Exception as exc:
            logger.warning(
                "Redis geo unavailable, falling back to DB only: %s", exc,
            )
            self._geo = None

    def get_handled_event_types(self) -> Optional[Set[str]]:
        return {
            EventType.DRIVER_LOCATION_UPDATED.value,
            EventType.DRIVER_AVAILABILITY_UPDATED.value,
        }

    def handle_event(self, envelope: EventEnvelope) -> None:
        """Dispatch a driver event to the appropriate handler."""
        payload = envelope.typed_payload()

        if envelope.event_type == EventType.DRIVER_LOCATION_UPDATED.value:
            self._handle_location_update(payload)

        elif envelope.event_type == EventType.DRIVER_AVAILABILITY_UPDATED.value:
            self._handle_availability_update(envelope, payload)

    # ── Location updates (high frequency, no dedup) ────────────────────────

    def _handle_location_update(
        self, payload: DriverLocationPayload,
    ) -> None:
        """Update driver location in Redis and PostgreSQL."""
        driver_id = payload.driver_id

        # 1. Update Redis geo index (fast path)
        if self._geo:
            self._geo.update_driver_location(
                driver_id=driver_id,
                lat=payload.latitude,
                lng=payload.longitude,
            )

        # 2. Upsert PostgreSQL (durable record)
        db = SessionLocal()
        try:
            location = (
                db.query(DriverLocation)
                .filter(DriverLocation.driver_id == driver_id)
                .first()
            )

            if location:
                location.latitude = payload.latitude
                location.longitude = payload.longitude
                location.updated_at = datetime.now(timezone.utc)
            else:
                location = DriverLocation(
                    driver_id=driver_id,
                    latitude=payload.latitude,
                    longitude=payload.longitude,
                )
                db.add(location)

            db.commit()

            logger.debug(
                "Driver location updated: driver_id=%d lat=%.4f lng=%.4f",
                driver_id,
                payload.latitude,
                payload.longitude,
            )

        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to update driver %d location in DB: %s",
                driver_id,
                exc,
            )
            raise
        finally:
            db.close()

    # ── Availability updates (deduplicated) ────────────────────────────────

    def _handle_availability_update(
        self,
        envelope: EventEnvelope,
        payload: DriverAvailabilityPayload,
    ) -> None:
        """Update driver availability in PostgreSQL and Redis."""
        db = SessionLocal()
        try:
            # Idempotency check (availability events only)
            if OutboxRepository.is_event_processed(db, envelope.event_id):
                logger.debug(
                    "Duplicate availability event skipped: %s",
                    envelope.event_id,
                )
                self.metrics.record_duplicate()
                return

            driver_id = payload.driver_id

            # Update ActiveDriver
            active = (
                db.query(ActiveDriver)
                .filter(ActiveDriver.driver_id == driver_id)
                .first()
            )

            if active:
                active.is_online = payload.is_online
                active.is_available = payload.is_available
                active.last_seen = datetime.now(timezone.utc)
            else:
                active = ActiveDriver(
                    driver_id=driver_id,
                    is_online=payload.is_online,
                    is_available=payload.is_available,
                    last_seen=datetime.now(timezone.utc),
                )
                db.add(active)

            # Update Redis geo index
            if self._geo:
                if not payload.is_online:
                    self._geo.remove_driver(driver_id)
                    logger.info(
                        "Driver %d went offline, removed from geo index.",
                        driver_id,
                    )

            # Mark processed
            OutboxRepository.mark_event_processed(
                db,
                envelope.event_id,
                envelope.event_type,
                self._group_id,
            )
            db.commit()

            logger.info(
                "Driver availability updated: driver_id=%d online=%s available=%s",
                driver_id,
                payload.is_online,
                payload.is_available,
            )

        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to update driver %d availability: %s",
                payload.driver_id,
                exc,
            )
            raise
        finally:
            db.close()


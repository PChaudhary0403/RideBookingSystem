"""
Ride lifecycle consumer.

Processes ride events from the ``ridebooking.rides.v1`` topic:
- ``ride.requested``       — triggers driver matching
- ``ride.driver.accepted`` — notifies the user via WebSocket
- ``ride.driver.rejected`` — re-triggers matching with the next driver
- ``ride.cancelled``       — releases the assigned driver
- ``ride.completed``       — releases the driver, logs analytics

This consumer runs in a dedicated thread via the consumer runner.
It uses the transactional outbox for idempotency (deduplication)
and the ``DriverMatchingService`` for automated driver assignment.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Set

from DataBase.Connection import SessionLocal
from DynamicDB.models.active_riders import ActiveDriver
from DynamicDB.models.triprequest import TripRequest
from DynamicDB.websockets.manager import manager
from kafka.consumer import BaseKafkaConsumer
from kafka.outbox.repository import OutboxRepository
from kafka.schemas import (
    EventEnvelope,
    EventType,
    RideRequestedPayload,
    RideDriverAcceptedPayload,
    RideDriverRejectedPayload,
    RideCancelledPayload,
    RideCompletedPayload,
)
from kafka.topics import Topics

logger = logging.getLogger(__name__)


def _ws_send(role: str, client_id: int, data: dict) -> None:
    """Send a WebSocket message from a synchronous consumer thread.

    The WebSocket manager is async; we bridge to it from a sync
    context using ``asyncio.run()``.  Failures are logged but
    never propagate — a missed WebSocket push is non-fatal.
    """
    try:
        asyncio.run(manager.send(role, client_id, data))
    except Exception as exc:
        logger.warning(
            "WebSocket send failed (role=%s, id=%d): %s",
            role,
            client_id,
            exc,
        )


class RideLifecycleConsumer(BaseKafkaConsumer):
    """Processes ride lifecycle events from the rides topic.

    Consumer group: ``ridebooking-ride-lifecycle``
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            group_id="ridebooking-ride-lifecycle",
            topics=[Topics.RIDES],
            **kwargs,
        )

    def get_handled_event_types(self) -> Optional[Set[str]]:
        return {
            EventType.RIDE_REQUESTED.value,
            EventType.RIDE_DRIVER_ACCEPTED.value,
            EventType.RIDE_DRIVER_REJECTED.value,
            EventType.RIDE_CANCELLED.value,
            EventType.RIDE_COMPLETED.value,
        }

    def handle_event(self, envelope: EventEnvelope) -> None:
        """Dispatch a ride event to the appropriate handler."""
        db = SessionLocal()
        try:
            # Idempotency check
            if OutboxRepository.is_event_processed(db, envelope.event_id):
                logger.debug(
                    "Duplicate event skipped: id=%s type=%s",
                    envelope.event_id,
                    envelope.event_type,
                )
                self.metrics.record_duplicate()
                return

            payload = envelope.typed_payload()

            if envelope.event_type == EventType.RIDE_REQUESTED.value:
                self._handle_ride_requested(db, payload)

            elif envelope.event_type == EventType.RIDE_DRIVER_ACCEPTED.value:
                self._handle_ride_accepted(db, payload)

            elif envelope.event_type == EventType.RIDE_DRIVER_REJECTED.value:
                self._handle_ride_rejected(db, payload)

            elif envelope.event_type == EventType.RIDE_CANCELLED.value:
                self._handle_ride_cancelled(db, payload)

            elif envelope.event_type == EventType.RIDE_COMPLETED.value:
                self._handle_ride_completed(db, payload)

            # Mark processed (in same transaction as any business changes)
            OutboxRepository.mark_event_processed(
                db,
                envelope.event_id,
                envelope.event_type,
                self._group_id,
            )
            db.commit()

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── Event handlers ─────────────────────────────────────────────────────

    def _handle_ride_requested(
        self, db, payload: RideRequestedPayload,
    ) -> None:
        """Trigger automatic driver matching for a new ride request."""
        logger.info(
            "Processing ride.requested: ride_id=%d user_id=%d",
            payload.ride_id,
            payload.user_id,
        )

        try:
            from services.driver_matching_service import DriverMatchingService

            matcher = DriverMatchingService()
            result = matcher.assign_best_driver(
                db,
                trip_req_id=payload.ride_id,
                pickup_lat=payload.pickup_lat,
                pickup_lng=payload.pickup_lng,
            )

            if result:
                driver_id, distance_km = result
                logger.info(
                    "Driver matched: ride_id=%d driver_id=%d distance=%.2f km",
                    payload.ride_id,
                    driver_id,
                    distance_km,
                )
                # Notify the driver via WebSocket
                _ws_send("driver", driver_id, {
                    "type": "new request",
                    "request": {
                        "trip_req_id": payload.ride_id,
                        "user_id": payload.user_id,
                        "pickup_lat": payload.pickup_lat,
                        "pickup_long": payload.pickup_lng,
                        "dest_lat": payload.dest_lat,
                        "dest_long": payload.dest_lng,
                    },
                })
            else:
                logger.warning(
                    "No available drivers for ride_id=%d", payload.ride_id,
                )

        except Exception as exc:
            logger.error(
                "Driver matching failed for ride_id=%d: %s",
                payload.ride_id,
                exc,
                exc_info=True,
            )

    def _handle_ride_accepted(
        self, db, payload: RideDriverAcceptedPayload,
    ) -> None:
        """Notify the user that their ride was accepted."""
        logger.info(
            "Processing ride.driver.accepted: ride_id=%d driver_id=%d",
            payload.ride_id,
            payload.driver_id,
        )

        trip = (
            db.query(TripRequest)
            .filter(TripRequest.id == payload.ride_id)
            .first()
        )
        if trip:
            _ws_send("user", trip.user_id, {
                "type": "driver_response",
                "trip_req_id": trip.id,
                "status": "accepted",
                "driver_id": payload.driver_id,
            })

    def _handle_ride_rejected(
        self, db, payload: RideDriverRejectedPayload,
    ) -> None:
        """Re-trigger matching after a driver rejection."""
        logger.info(
            "Processing ride.driver.rejected: ride_id=%d driver_id=%d",
            payload.ride_id,
            payload.driver_id,
        )

        if not payload.retry_eligible:
            logger.info(
                "Rejection not retry-eligible for ride_id=%d",
                payload.ride_id,
            )
            return

        trip = (
            db.query(TripRequest)
            .filter(TripRequest.id == payload.ride_id)
            .first()
        )
        if not trip:
            return

        # Notify user of rejection
        _ws_send("user", trip.user_id, {
            "type": "driver_response",
            "trip_req_id": trip.id,
            "status": "rejected",
        })

        # Attempt to find another driver
        try:
            from services.driver_matching_service import DriverMatchingService

            matcher = DriverMatchingService()
            result = matcher.assign_best_driver(
                db,
                trip_req_id=trip.id,
                pickup_lat=trip.pickup_lat,
                pickup_lng=trip.pickup_long,
            )

            if result:
                driver_id, dist = result
                logger.info(
                    "Re-matched ride_id=%d to driver_id=%d (%.2f km)",
                    trip.id,
                    driver_id,
                    dist,
                )
                _ws_send("driver", driver_id, {
                    "type": "new request",
                    "request": {
                        "trip_req_id": trip.id,
                        "user_id": trip.user_id,
                        "pickup_lat": trip.pickup_lat,
                        "pickup_long": trip.pickup_long,
                        "dest_lat": trip.dest_lat,
                        "dest_long": trip.dest_long,
                    },
                })
            else:
                logger.warning(
                    "No alternative drivers for ride_id=%d", trip.id,
                )

        except Exception as exc:
            logger.error(
                "Re-matching failed for ride_id=%d: %s",
                trip.id,
                exc,
                exc_info=True,
            )

    def _handle_ride_cancelled(
        self, db, payload: RideCancelledPayload,
    ) -> None:
        """Release the assigned driver on cancellation."""
        logger.info(
            "Processing ride.cancelled: ride_id=%d by=%s",
            payload.ride_id,
            payload.cancelled_by,
        )

        trip = (
            db.query(TripRequest)
            .filter(TripRequest.id == payload.ride_id)
            .first()
        )
        if trip and trip.driver_id:
            driver = (
                db.query(ActiveDriver)
                .filter(ActiveDriver.driver_id == trip.driver_id)
                .first()
            )
            if driver:
                driver.is_available = True

            # Notify the driver
            _ws_send("driver", trip.driver_id, {
                "type": "ride_cancelled",
                "trip_req_id": trip.id,
                "reason": payload.reason or "cancelled",
            })

    def _handle_ride_completed(
        self, db, payload: RideCompletedPayload,
    ) -> None:
        """Release the driver and notify parties on completion."""
        logger.info(
            "Processing ride.completed: ride_id=%d driver_id=%d",
            payload.ride_id,
            payload.driver_id,
        )

        # Release driver
        driver = (
            db.query(ActiveDriver)
            .filter(ActiveDriver.driver_id == payload.driver_id)
            .first()
        )
        if driver:
            driver.is_available = True

        # Notify user
        _ws_send("user", payload.user_id, {
            "type": "ride_completed",
            "trip_req_id": payload.ride_id,
        })


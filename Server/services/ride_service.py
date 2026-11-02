"""
Ride lifecycle service.

Manages the complete ride lifecycle — from request through completion —
with atomic Kafka event emission via the transactional outbox pattern.

All state mutations and outbox writes occur within a single database
transaction to guarantee exactly-once semantics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from DynamicDB.models.triprequest import TripRequest
from DynamicDB.models.active_riders import ActiveDriver
from kafka.schemas import (
    EventEnvelope,
    EventType,
    RideRequestedPayload,
    RideDriverAcceptedPayload,
    RideDriverRejectedPayload,
    RideCancelledPayload,
    RideStartedPayload,
    RideCompletedPayload,
    RideStatus,
    validate_transition,
)
from kafka.outbox.repository import OutboxRepository
from kafka.topics import Topics

logger = logging.getLogger(__name__)


# ── Status mapping helpers ─────────────────────────────────────────────────

# Map legacy string statuses stored in the DB to RideStatus enum values.
_STATUS_MAP = {
    "pending": RideStatus.REQUESTED,
    "requested": RideStatus.REQUESTED,
    "matching": RideStatus.MATCHING,
    "assigned": RideStatus.DRIVER_ASSIGNED,
    "driver_assigned": RideStatus.DRIVER_ASSIGNED,
    "accepted": RideStatus.ACCEPTED,
    "driver_en_route": RideStatus.DRIVER_EN_ROUTE,
    "driver_arrived": RideStatus.DRIVER_ARRIVED,
    "in_progress": RideStatus.IN_PROGRESS,
    "completed": RideStatus.COMPLETED,
    "cancelled": RideStatus.CANCELLED,
}


def _to_ride_status(raw_status: str) -> RideStatus:
    """Convert a raw DB status string to a ``RideStatus`` enum value.

    Args:
        raw_status: The status string stored in the database.

    Returns:
        The corresponding ``RideStatus`` enum member.

    Raises:
        ValueError: If the status string is not recognised.
    """
    status = _STATUS_MAP.get(raw_status.lower())
    if status is None:
        raise ValueError(f"Unknown ride status: {raw_status!r}")
    return status


def _assert_transition(current_raw: str, target: RideStatus) -> None:
    """Validate that a ride status transition is allowed.

    Args:
        current_raw: Current status string from the database.
        target: Desired ``RideStatus`` to transition to.

    Raises:
        ValueError: If the transition is invalid.
    """
    current = _to_ride_status(current_raw)
    if not validate_transition(current, target):
        raise ValueError(
            f"Invalid status transition: {current.value!r} → {target.value!r}"
        )


def _lock_trip(db: Session, trip_req_id: int) -> TripRequest:
    """Fetch a ``TripRequest`` with a row-level lock.

    Uses ``SELECT … FOR UPDATE`` on PostgreSQL.  Falls back to a plain
    SELECT on databases that do not support row locking (e.g. SQLite in
    tests).

    Args:
        db: Active SQLAlchemy session.
        trip_req_id: Primary key of the trip request.

    Returns:
        The locked ``TripRequest`` instance.

    Raises:
        ValueError: If no trip request with the given ID exists.
    """
    try:
        trip = (
            db.query(TripRequest)
            .filter(TripRequest.id == trip_req_id)
            .with_for_update()
            .first()
        )
    except Exception:
        # SQLite (used in tests) doesn't support FOR UPDATE
        trip = (
            db.query(TripRequest)
            .filter(TripRequest.id == trip_req_id)
            .first()
        )

    if trip is None:
        raise ValueError(f"TripRequest {trip_req_id} not found")
    return trip


class RideLifecycleService:
    """Orchestrates ride lifecycle transitions with transactional outbox events.

    Every public method performs the business state change **and** inserts
    the corresponding outbox event within a single DB transaction, then
    commits exactly once.
    """

    # ── 1. Request a ride ──────────────────────────────────────────────────

    @staticmethod
    def request_ride(
        db: Session,
        user_id: int,
        driver_id: int,
        pickup_lat: float,
        pickup_long: float,
        dest_lat: float,
        dest_long: float,
    ) -> TripRequest:
        """Create a new ride request and emit a ``RIDE_REQUESTED`` event.

        Args:
            db: Active SQLAlchemy session.
            user_id: ID of the requesting user.
            driver_id: ID of the target driver.
            pickup_lat: Pickup latitude.
            pickup_long: Pickup longitude.
            dest_lat: Destination latitude.
            dest_long: Destination longitude.

        Returns:
            The newly created ``TripRequest``.
        """
        trip = TripRequest(
            user_id=user_id,
            driver_id=driver_id,
            pickup_lat=pickup_lat,
            pickup_long=pickup_long,
            dest_lat=dest_lat,
            dest_long=dest_long,
            status="pending",
        )
        db.add(trip)
        # Flush to obtain the auto-generated ``trip.id`` before building
        # the event payload, without committing the transaction.
        db.flush()

        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_REQUESTED,
            aggregate_type="ride",
            aggregate_id=str(trip.id),
            payload=RideRequestedPayload(
                ride_id=trip.id,
                user_id=user_id,
                pickup_lat=pickup_lat,
                pickup_lng=pickup_long,
                dest_lat=dest_lat,
                dest_lng=dest_long,
            ),
            source="ride-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.RIDES, envelope)

        db.commit()
        logger.info(
            "Ride requested: trip_id=%d user=%d driver=%d",
            trip.id,
            user_id,
            driver_id,
        )
        return trip

    # ── 2. Accept a ride ───────────────────────────────────────────────────

    @staticmethod
    def accept_ride(
        db: Session,
        trip_req_id: int,
        driver_id: int,
    ) -> TripRequest:
        """Accept a ride request and mark the driver as unavailable.

        Uses ``SELECT FOR UPDATE`` to prevent concurrent acceptance by
        another driver or duplicate acceptance.

        Args:
            db: Active SQLAlchemy session.
            trip_req_id: ID of the trip request to accept.
            driver_id: ID of the accepting driver.

        Returns:
            The updated ``TripRequest``.

        Raises:
            ValueError: If the trip is not found or the transition is invalid.
        """
        trip = _lock_trip(db, trip_req_id)
        _assert_transition(trip.status, RideStatus.ACCEPTED)

        trip.status = "accepted"
        trip.driver_id = driver_id
        trip.updated_at = datetime.now(timezone.utc)

        # Mark driver unavailable
        driver = (
            db.query(ActiveDriver)
            .filter(ActiveDriver.driver_id == driver_id)
            .first()
        )
        if driver:
            driver.is_available = False

        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_DRIVER_ACCEPTED,
            aggregate_type="ride",
            aggregate_id=str(trip.id),
            payload=RideDriverAcceptedPayload(
                ride_id=trip.id,
                driver_id=driver_id,
            ),
            source="ride-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.RIDES, envelope)

        db.commit()
        logger.info(
            "Ride accepted: trip_id=%d driver=%d",
            trip.id,
            driver_id,
        )
        return trip

    # ── 3. Reject a ride ───────────────────────────────────────────────────

    @staticmethod
    def reject_ride(
        db: Session,
        trip_req_id: int,
        driver_id: int,
    ) -> TripRequest:
        """Reject a ride request and set the status back to pending.

        Args:
            db: Active SQLAlchemy session.
            trip_req_id: ID of the trip request to reject.
            driver_id: ID of the rejecting driver.

        Returns:
            The updated ``TripRequest``.

        Raises:
            ValueError: If the trip is not found or the transition is invalid.
        """
        trip = _lock_trip(db, trip_req_id)
        _assert_transition(trip.status, RideStatus.MATCHING)

        trip.status = "pending"
        trip.updated_at = datetime.now(timezone.utc)

        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_DRIVER_REJECTED,
            aggregate_type="ride",
            aggregate_id=str(trip.id),
            payload=RideDriverRejectedPayload(
                ride_id=trip.id,
                driver_id=driver_id,
                reason="rejected",
            ),
            source="ride-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.RIDES, envelope)

        db.commit()
        logger.info(
            "Ride rejected: trip_id=%d driver=%d",
            trip.id,
            driver_id,
        )
        return trip

    # ── 4. Cancel a ride ───────────────────────────────────────────────────

    @staticmethod
    def cancel_ride(
        db: Session,
        trip_req_id: int,
        user_id: int,
        cancelled_by: str = "user",
    ) -> TripRequest:
        """Cancel an active ride request.

        Args:
            db: Active SQLAlchemy session.
            trip_req_id: ID of the trip request to cancel.
            user_id: ID of the user requesting cancellation.
            cancelled_by: Who initiated the cancellation
                          (``"user"``, ``"driver"``, or ``"system"``).

        Returns:
            The updated ``TripRequest``.

        Raises:
            ValueError: If the trip is not found or the transition is invalid.
        """
        trip = _lock_trip(db, trip_req_id)
        _assert_transition(trip.status, RideStatus.CANCELLED)

        # If a driver was assigned, release them
        if trip.driver_id:
            driver = (
                db.query(ActiveDriver)
                .filter(ActiveDriver.driver_id == trip.driver_id)
                .first()
            )
            if driver:
                driver.is_available = True

        trip.status = "cancelled"
        trip.updated_at = datetime.now(timezone.utc)

        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_CANCELLED,
            aggregate_type="ride",
            aggregate_id=str(trip.id),
            payload=RideCancelledPayload(
                ride_id=trip.id,
                cancelled_by=cancelled_by,
            ),
            source="ride-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.RIDES, envelope)

        db.commit()
        logger.info(
            "Ride cancelled: trip_id=%d cancelled_by=%s",
            trip.id,
            cancelled_by,
        )
        return trip

    # ── 5. Start a ride ────────────────────────────────────────────────────

    @staticmethod
    def start_ride(
        db: Session,
        trip_req_id: int,
        driver_id: int,
    ) -> TripRequest:
        """Mark a ride as in progress.

        Args:
            db: Active SQLAlchemy session.
            trip_req_id: ID of the trip request.
            driver_id: ID of the driver starting the ride.

        Returns:
            The updated ``TripRequest``.

        Raises:
            ValueError: If the trip is not found or the transition is invalid.
        """
        trip = _lock_trip(db, trip_req_id)
        _assert_transition(trip.status, RideStatus.IN_PROGRESS)

        trip.status = "in_progress"
        trip.updated_at = datetime.now(timezone.utc)

        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_STARTED,
            aggregate_type="ride",
            aggregate_id=str(trip.id),
            payload=RideStartedPayload(
                ride_id=trip.id,
                driver_id=driver_id,
            ),
            source="ride-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.RIDES, envelope)

        db.commit()
        logger.info(
            "Ride started: trip_id=%d driver=%d",
            trip.id,
            driver_id,
        )
        return trip

    # ── 6. Complete a ride ─────────────────────────────────────────────────

    @staticmethod
    def complete_ride(
        db: Session,
        trip_req_id: int,
        driver_id: int,
    ) -> TripRequest:
        """Mark a ride as completed and release the driver.

        Args:
            db: Active SQLAlchemy session.
            trip_req_id: ID of the trip request.
            driver_id: ID of the driver completing the ride.

        Returns:
            The updated ``TripRequest``.

        Raises:
            ValueError: If the trip is not found or the transition is invalid.
        """
        trip = _lock_trip(db, trip_req_id)
        _assert_transition(trip.status, RideStatus.COMPLETED)

        trip.status = "completed"
        trip.updated_at = datetime.now(timezone.utc)

        # Release the driver back to the available pool
        driver = (
            db.query(ActiveDriver)
            .filter(ActiveDriver.driver_id == driver_id)
            .first()
        )
        if driver:
            driver.is_available = True

        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_COMPLETED,
            aggregate_type="ride",
            aggregate_id=str(trip.id),
            payload=RideCompletedPayload(
                ride_id=trip.id,
                driver_id=driver_id,
                user_id=trip.user_id,
            ),
            source="ride-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.RIDES, envelope)

        db.commit()
        logger.info(
            "Ride completed: trip_id=%d driver=%d",
            trip.id,
            driver_id,
        )
        return trip

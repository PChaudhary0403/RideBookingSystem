"""
Notification service.

Emits notification events through the transactional outbox so they are
delivered reliably alongside business state changes.  Does **not** send
notifications directly — downstream consumers read from the
``NOTIFICATIONS`` topic and handle delivery (push, SMS, email, etc.).
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from kafka.schemas import (
    EventEnvelope,
    EventType,
    NotificationRequestedPayload,
)
from kafka.outbox.repository import OutboxRepository
from kafka.topics import Topics

logger = logging.getLogger(__name__)


class NotificationService:
    """Emits notification events through the transactional outbox."""

    @staticmethod
    def notify_driver_new_request(
        db: Session,
        driver_id: int,
        trip_req_id: int,
        pickup_lat: float,
        pickup_lng: float,
    ) -> None:
        """Queue a notification for a driver about a new ride request.

        Args:
            db: Active SQLAlchemy session (caller manages the transaction).
            driver_id: ID of the driver to notify.
            trip_req_id: ID of the ride request.
            pickup_lat: Pickup latitude.
            pickup_lng: Pickup longitude.
        """
        envelope = EventEnvelope.create(
            event_type=EventType.NOTIFICATION_REQUESTED,
            aggregate_type="notification",
            aggregate_id=str(trip_req_id),
            payload=NotificationRequestedPayload(
                recipient_role="driver",
                recipient_id=driver_id,
                notification_type="ride_request",
                title="New Ride Request",
                body=f"New ride request #{trip_req_id} near ({pickup_lat:.4f}, {pickup_lng:.4f}).",
                data={
                    "trip_req_id": trip_req_id,
                    "pickup_lat": pickup_lat,
                    "pickup_lng": pickup_lng,
                },
            ),
            source="notification-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.NOTIFICATIONS, envelope)
        logger.info(
            "Notification queued: driver=%d type=ride_request trip=%d",
            driver_id,
            trip_req_id,
        )

    @staticmethod
    def notify_user_ride_accepted(
        db: Session,
        user_id: int,
        trip_req_id: int,
        driver_id: int,
    ) -> None:
        """Queue a notification for a user that their ride was accepted.

        Args:
            db: Active SQLAlchemy session.
            user_id: ID of the user to notify.
            trip_req_id: ID of the ride request.
            driver_id: ID of the driver who accepted.
        """
        envelope = EventEnvelope.create(
            event_type=EventType.NOTIFICATION_REQUESTED,
            aggregate_type="notification",
            aggregate_id=str(trip_req_id),
            payload=NotificationRequestedPayload(
                recipient_role="user",
                recipient_id=user_id,
                notification_type="ride_accepted",
                title="Ride Accepted",
                body=f"Driver #{driver_id} has accepted your ride request #{trip_req_id}.",
                data={
                    "trip_req_id": trip_req_id,
                    "driver_id": driver_id,
                },
            ),
            source="notification-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.NOTIFICATIONS, envelope)
        logger.info(
            "Notification queued: user=%d type=ride_accepted trip=%d",
            user_id,
            trip_req_id,
        )

    @staticmethod
    def notify_user_ride_rejected(
        db: Session,
        user_id: int,
        trip_req_id: int,
    ) -> None:
        """Queue a notification for a user that their ride was rejected.

        Args:
            db: Active SQLAlchemy session.
            user_id: ID of the user to notify.
            trip_req_id: ID of the ride request.
        """
        envelope = EventEnvelope.create(
            event_type=EventType.NOTIFICATION_REQUESTED,
            aggregate_type="notification",
            aggregate_id=str(trip_req_id),
            payload=NotificationRequestedPayload(
                recipient_role="user",
                recipient_id=user_id,
                notification_type="ride_rejected",
                title="Ride Rejected",
                body=f"Your ride request #{trip_req_id} was rejected. We are looking for another driver.",
                data={
                    "trip_req_id": trip_req_id,
                },
            ),
            source="notification-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.NOTIFICATIONS, envelope)
        logger.info(
            "Notification queued: user=%d type=ride_rejected trip=%d",
            user_id,
            trip_req_id,
        )

    @staticmethod
    def notify_ride_cancelled(
        db: Session,
        recipient_role: str,
        recipient_id: int,
        trip_req_id: int,
        cancelled_by: str,
    ) -> None:
        """Queue a cancellation notification.

        Args:
            db: Active SQLAlchemy session.
            recipient_role: ``"user"`` or ``"driver"``.
            recipient_id: ID of the recipient.
            trip_req_id: ID of the cancelled ride request.
            cancelled_by: Who initiated the cancellation
                          (``"user"``, ``"driver"``, or ``"system"``).
        """
        envelope = EventEnvelope.create(
            event_type=EventType.NOTIFICATION_REQUESTED,
            aggregate_type="notification",
            aggregate_id=str(trip_req_id),
            payload=NotificationRequestedPayload(
                recipient_role=recipient_role,
                recipient_id=recipient_id,
                notification_type="ride_cancelled",
                title="Ride Cancelled",
                body=f"Ride request #{trip_req_id} has been cancelled by {cancelled_by}.",
                data={
                    "trip_req_id": trip_req_id,
                    "cancelled_by": cancelled_by,
                },
            ),
            source="notification-service",
        )
        OutboxRepository.create_event_from_envelope(db, Topics.NOTIFICATIONS, envelope)
        logger.info(
            "Notification queued: %s=%d type=ride_cancelled trip=%d cancelled_by=%s",
            recipient_role,
            recipient_id,
            trip_req_id,
            cancelled_by,
        )

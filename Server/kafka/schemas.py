"""
Event schema definitions for the Kafka event-driven pipeline.

Every Kafka message uses a standardized JSON envelope wrapping an
event-specific payload.  All schemas are Pydantic v2 models for
runtime validation, serialization, and documentation.

Usage::

    from kafka.schemas import EventEnvelope, RideRequestedPayload

    event = EventEnvelope.create(
        event_type="ride.requested",
        aggregate_type="ride",
        aggregate_id=str(ride.id),
        payload=RideRequestedPayload(
            ride_id=ride.id,
            user_id=42,
            pickup_lat=19.076,
            pickup_lng=72.877,
            dest_lat=19.229,
            dest_lng=72.856,
        ),
        source="ride-service",
    )
    raw = event.serialize()   # bytes for Kafka value
    back = EventEnvelope.deserialize(raw)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field


# ── helpers ────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ── Event types ────────────────────────────────────────────────────────────

class EventType(str, Enum):
    """All recognised event types across the system."""

    # Ride lifecycle
    RIDE_REQUESTED = "ride.requested"
    RIDE_CREATED = "ride.created"
    RIDE_ASSIGNMENT_STARTED = "ride.assignment.started"
    RIDE_DRIVER_ASSIGNED = "ride.driver.assigned"
    RIDE_DRIVER_ACCEPTED = "ride.driver.accepted"
    RIDE_DRIVER_REJECTED = "ride.driver.rejected"
    RIDE_CANCELLED = "ride.cancelled"
    RIDE_STARTED = "ride.started"
    RIDE_COMPLETED = "ride.completed"

    # Driver lifecycle
    DRIVER_AVAILABILITY_UPDATED = "driver.availability.updated"
    DRIVER_LOCATION_UPDATED = "driver.location.updated"
    DRIVER_STATUS_CHANGED = "driver.status.changed"

    # Notifications
    NOTIFICATION_REQUESTED = "notification.requested"
    NOTIFICATION_DELIVERED = "notification.delivered"
    NOTIFICATION_FAILED = "notification.failed"


# ── Ride status (state machine) ────────────────────────────────────────────

class RideStatus(str, Enum):
    """Canonical ride statuses enforced by the state machine."""

    REQUESTED = "requested"
    MATCHING = "matching"
    DRIVER_ASSIGNED = "driver_assigned"
    ACCEPTED = "accepted"
    DRIVER_EN_ROUTE = "driver_en_route"
    DRIVER_ARRIVED = "driver_arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Valid state transitions: {from_status: [allowed_to_statuses]}
VALID_TRANSITIONS: Dict[RideStatus, list[RideStatus]] = {
    RideStatus.REQUESTED: [RideStatus.MATCHING, RideStatus.CANCELLED],
    RideStatus.MATCHING: [
        RideStatus.DRIVER_ASSIGNED,
        RideStatus.CANCELLED,
    ],
    RideStatus.DRIVER_ASSIGNED: [
        RideStatus.ACCEPTED,
        RideStatus.MATCHING,       # rejection / timeout → retry
        RideStatus.CANCELLED,
    ],
    RideStatus.ACCEPTED: [
        RideStatus.DRIVER_EN_ROUTE,
        RideStatus.CANCELLED,
    ],
    RideStatus.DRIVER_EN_ROUTE: [
        RideStatus.DRIVER_ARRIVED,
        RideStatus.CANCELLED,
    ],
    RideStatus.DRIVER_ARRIVED: [
        RideStatus.IN_PROGRESS,
        RideStatus.CANCELLED,
    ],
    RideStatus.IN_PROGRESS: [
        RideStatus.COMPLETED,
    ],
    # Terminal states — no transitions out
    RideStatus.COMPLETED: [],
    RideStatus.CANCELLED: [],
}


def validate_transition(from_status: RideStatus, to_status: RideStatus) -> bool:
    """Check whether a ride status transition is allowed.

    Args:
        from_status: The current ride status.
        to_status: The desired new status.

    Returns:
        True if the transition is valid, False otherwise.
    """
    allowed = VALID_TRANSITIONS.get(from_status, [])
    return to_status in allowed


# ── Event payloads ─────────────────────────────────────────────────────────

class RideRequestedPayload(BaseModel):
    """Payload for ``ride.requested`` events."""

    ride_id: int
    user_id: int
    pickup_lat: float = Field(..., ge=-90.0, le=90.0)
    pickup_lng: float = Field(..., ge=-180.0, le=180.0)
    dest_lat: float = Field(..., ge=-90.0, le=90.0)
    dest_lng: float = Field(..., ge=-180.0, le=180.0)
    requested_at: datetime = Field(default_factory=_utcnow)


class RideAssignmentStartedPayload(BaseModel):
    """Payload for ``ride.assignment.started`` events."""

    ride_id: int
    attempt: int = 1
    search_radius_km: float = 5.0
    started_at: datetime = Field(default_factory=_utcnow)


class RideDriverAssignedPayload(BaseModel):
    """Payload for ``ride.driver.assigned`` events."""

    ride_id: int
    driver_id: int
    assignment_attempt: int = 1
    assigned_at: datetime = Field(default_factory=_utcnow)


class RideDriverAcceptedPayload(BaseModel):
    """Payload for ``ride.driver.accepted`` events."""

    ride_id: int
    driver_id: int
    accepted_at: datetime = Field(default_factory=_utcnow)


class RideDriverRejectedPayload(BaseModel):
    """Payload for ``ride.driver.rejected`` events."""

    ride_id: int
    driver_id: int
    reason: str = "rejected"
    rejected_at: datetime = Field(default_factory=_utcnow)
    retry_eligible: bool = True


class RideCancelledPayload(BaseModel):
    """Payload for ``ride.cancelled`` events."""

    ride_id: int
    cancelled_by: str           # "user" | "driver" | "system"
    reason: Optional[str] = None
    cancelled_at: datetime = Field(default_factory=_utcnow)


class RideStartedPayload(BaseModel):
    """Payload for ``ride.started`` events."""

    ride_id: int
    driver_id: int
    started_at: datetime = Field(default_factory=_utcnow)


class RideCompletedPayload(BaseModel):
    """Payload for ``ride.completed`` events."""

    ride_id: int
    driver_id: int
    user_id: int
    completed_at: datetime = Field(default_factory=_utcnow)


class DriverAvailabilityPayload(BaseModel):
    """Payload for ``driver.availability.updated`` events."""

    driver_id: int
    is_online: bool
    is_available: bool
    changed_at: datetime = Field(default_factory=_utcnow)


class DriverLocationPayload(BaseModel):
    """Payload for ``driver.location.updated`` events."""

    driver_id: int
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    heading: Optional[float] = None
    speed_kmh: Optional[float] = None
    accuracy_m: Optional[float] = None
    captured_at: datetime = Field(default_factory=_utcnow)


class NotificationRequestedPayload(BaseModel):
    """Payload for ``notification.requested`` events."""

    recipient_role: str             # "user" | "driver"
    recipient_id: int
    notification_type: str          # "ride_update", "driver_response", etc.
    title: str
    body: str
    data: Dict[str, Any] = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=_utcnow)


class NotificationDeliveredPayload(BaseModel):
    """Payload for ``notification.delivered`` events."""

    recipient_role: str
    recipient_id: int
    notification_type: str
    delivered_at: datetime = Field(default_factory=_utcnow)


class NotificationFailedPayload(BaseModel):
    """Payload for ``notification.failed`` events."""

    recipient_role: str
    recipient_id: int
    notification_type: str
    error: str
    failed_at: datetime = Field(default_factory=_utcnow)


class RideCreatedPayload(BaseModel):
    """Payload for ``ride.created`` events (ride persisted in DB)."""

    ride_id: int
    user_id: int
    created_at: datetime = Field(default_factory=_utcnow)


class DriverStatusChangedPayload(BaseModel):
    """Payload for ``driver.status.changed`` events."""

    driver_id: int
    previous_status: str
    new_status: str
    changed_at: datetime = Field(default_factory=_utcnow)


# Map event types to their payload models for deserialization
PAYLOAD_MODELS: Dict[str, type[BaseModel]] = {
    EventType.RIDE_REQUESTED: RideRequestedPayload,
    EventType.RIDE_CREATED: RideCreatedPayload,
    EventType.RIDE_ASSIGNMENT_STARTED: RideAssignmentStartedPayload,
    EventType.RIDE_DRIVER_ASSIGNED: RideDriverAssignedPayload,
    EventType.RIDE_DRIVER_ACCEPTED: RideDriverAcceptedPayload,
    EventType.RIDE_DRIVER_REJECTED: RideDriverRejectedPayload,
    EventType.RIDE_CANCELLED: RideCancelledPayload,
    EventType.RIDE_STARTED: RideStartedPayload,
    EventType.RIDE_COMPLETED: RideCompletedPayload,
    EventType.DRIVER_AVAILABILITY_UPDATED: DriverAvailabilityPayload,
    EventType.DRIVER_LOCATION_UPDATED: DriverLocationPayload,
    EventType.DRIVER_STATUS_CHANGED: DriverStatusChangedPayload,
    EventType.NOTIFICATION_REQUESTED: NotificationRequestedPayload,
    EventType.NOTIFICATION_DELIVERED: NotificationDeliveredPayload,
    EventType.NOTIFICATION_FAILED: NotificationFailedPayload,
}


# ── Event envelope ─────────────────────────────────────────────────────────

class EventEnvelope(BaseModel):
    """Standardized envelope wrapping every Kafka event message.

    The envelope carries metadata (event_id for deduplication,
    correlation_id for tracing, aggregate_id for partitioning)
    alongside the event-specific payload.
    """

    event_id: str = Field(default_factory=_new_uuid)
    event_type: str
    event_version: int = 1
    timestamp: datetime = Field(default_factory=_utcnow)
    source: str = "ride-booking-system"
    correlation_id: str = Field(default_factory=_new_uuid)
    aggregate_id: str
    aggregate_type: str
    payload: Dict[str, Any]

    @classmethod
    def create(
        cls,
        event_type: Union[str, EventType],
        aggregate_type: str,
        aggregate_id: str,
        payload: BaseModel,
        source: str = "ride-booking-system",
        correlation_id: Optional[str] = None,
        event_version: int = 1,
    ) -> "EventEnvelope":
        """Factory method to build an envelope from a typed payload.

        Args:
            event_type: The event type string or EventType enum.
            aggregate_type: The entity type (``ride``, ``driver``, etc.).
            aggregate_id: The partition key value.
            payload: A Pydantic model with event-specific data.
            source: The producing service identifier.
            correlation_id: Optional tracing correlation ID.
            event_version: Schema version number.

        Returns:
            A fully populated EventEnvelope.
        """
        et = event_type.value if isinstance(event_type, EventType) else event_type
        return cls(
            event_type=et,
            event_version=event_version,
            source=source,
            correlation_id=correlation_id or _new_uuid(),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload.model_dump(mode="json"),
        )

    def serialize(self) -> bytes:
        """Serialize the envelope to UTF-8 JSON bytes for Kafka value."""
        return self.model_dump_json().encode("utf-8")

    @classmethod
    def deserialize(cls, raw: bytes) -> "EventEnvelope":
        """Deserialize a Kafka message value back into an EventEnvelope.

        Args:
            raw: The raw bytes from a Kafka message value.

        Returns:
            A validated EventEnvelope instance.
        """
        return cls.model_validate_json(raw)

    def typed_payload(self) -> BaseModel:
        """Deserialize the payload dict into the correct Pydantic model.

        Looks up the payload model from PAYLOAD_MODELS using
        ``self.event_type``.

        Returns:
            A typed payload model instance.

        Raises:
            ValueError: If the event_type has no registered payload model.
        """
        model_cls = PAYLOAD_MODELS.get(self.event_type)
        if model_cls is None:
            raise ValueError(
                f"No payload model registered for event type: {self.event_type}"
            )
        return model_cls.model_validate(self.payload)


# ── DLQ wrapper ────────────────────────────────────────────────────────────

class DLQEntry(BaseModel):
    """Dead Letter Queue entry wrapping a failed event with error context."""

    original_topic: str
    original_partition: Optional[int] = None
    original_offset: Optional[int] = None
    original_event: Dict[str, Any]
    error_message: str
    error_type: str
    retry_count: int = 0
    consumer_group: str = ""
    failed_at: datetime = Field(default_factory=_utcnow)

    def serialize(self) -> bytes:
        """Serialize to UTF-8 JSON bytes for Kafka value."""
        return self.model_dump_json().encode("utf-8")

    @classmethod
    def deserialize(cls, raw: bytes) -> "DLQEntry":
        """Deserialize from Kafka message value."""
        return cls.model_validate_json(raw)

"""
Unit tests for Kafka event schemas, serialization, and state machine.

Tests:
- EventEnvelope creation and serialization round-trip
- All payload model validation
- State machine transitions (valid + invalid)
- DLQ entry serialization
"""

import pytest
from datetime import datetime, timezone
from kafka.schemas import (
    EventEnvelope,
    EventType,
    RideStatus,
    VALID_TRANSITIONS,
    validate_transition,
    RideRequestedPayload,
    RideAssignmentStartedPayload,
    RideDriverAssignedPayload,
    RideDriverAcceptedPayload,
    RideDriverRejectedPayload,
    RideCancelledPayload,
    RideStartedPayload,
    RideCompletedPayload,
    DriverAvailabilityPayload,
    DriverLocationPayload,
    NotificationRequestedPayload,
    DLQEntry,
    PAYLOAD_MODELS,
)


# ── EventEnvelope tests ───────────────────────────────────────────────────

class TestEventEnvelope:
    """Tests for the EventEnvelope model."""

    def test_create_envelope(self):
        """Envelope.create() builds a valid envelope from a payload."""
        payload = RideRequestedPayload(
            ride_id=1,
            user_id=42,
            pickup_lat=19.076,
            pickup_lng=72.877,
            dest_lat=19.229,
            dest_lng=72.856,
        )
        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_REQUESTED,
            aggregate_type="ride",
            aggregate_id="1",
            payload=payload,
            source="test",
        )

        assert envelope.event_type == "ride.requested"
        assert envelope.aggregate_type == "ride"
        assert envelope.aggregate_id == "1"
        assert envelope.source == "test"
        assert envelope.event_version == 1
        assert len(envelope.event_id) == 36  # UUID format
        assert envelope.payload["ride_id"] == 1
        assert envelope.payload["user_id"] == 42

    def test_serialize_deserialize_roundtrip(self):
        """Envelope serialization and deserialization are inverse operations."""
        payload = RideRequestedPayload(
            ride_id=99,
            user_id=7,
            pickup_lat=28.644,
            pickup_lng=77.216,
            dest_lat=28.535,
            dest_lng=77.391,
        )
        original = EventEnvelope.create(
            event_type=EventType.RIDE_REQUESTED,
            aggregate_type="ride",
            aggregate_id="99",
            payload=payload,
        )

        raw = original.serialize()
        assert isinstance(raw, bytes)

        restored = EventEnvelope.deserialize(raw)
        assert restored.event_id == original.event_id
        assert restored.event_type == original.event_type
        assert restored.aggregate_id == original.aggregate_id
        assert restored.payload == original.payload

    def test_typed_payload(self):
        """typed_payload() returns the correct Pydantic model."""
        payload = RideDriverAcceptedPayload(ride_id=5, driver_id=10)
        envelope = EventEnvelope.create(
            event_type=EventType.RIDE_DRIVER_ACCEPTED,
            aggregate_type="ride",
            aggregate_id="5",
            payload=payload,
        )

        typed = envelope.typed_payload()
        assert isinstance(typed, RideDriverAcceptedPayload)
        assert typed.ride_id == 5
        assert typed.driver_id == 10

    def test_typed_payload_unknown_type(self):
        """typed_payload() raises ValueError for unknown event types."""
        envelope = EventEnvelope(
            event_type="unknown.event",
            aggregate_type="test",
            aggregate_id="1",
            payload={"foo": "bar"},
        )
        with pytest.raises(ValueError, match="No payload model"):
            envelope.typed_payload()

    def test_all_event_types_have_payload_models(self):
        """Every EventType enum member has a registered payload model."""
        for event_type in EventType:
            assert event_type.value in PAYLOAD_MODELS, (
                f"Missing payload model for {event_type.value}"
            )


# ── Payload validation tests ──────────────────────────────────────────────

class TestPayloadValidation:
    """Tests for payload model field validation."""

    def test_ride_requested_valid(self):
        p = RideRequestedPayload(
            ride_id=1, user_id=2,
            pickup_lat=19.0, pickup_lng=72.0,
            dest_lat=19.1, dest_lng=72.1,
        )
        assert p.ride_id == 1

    def test_ride_requested_invalid_lat(self):
        """Latitude must be between -90 and 90."""
        with pytest.raises(Exception):
            RideRequestedPayload(
                ride_id=1, user_id=2,
                pickup_lat=91.0, pickup_lng=72.0,
                dest_lat=19.1, dest_lng=72.1,
            )

    def test_ride_requested_invalid_lng(self):
        """Longitude must be between -180 and 180."""
        with pytest.raises(Exception):
            RideRequestedPayload(
                ride_id=1, user_id=2,
                pickup_lat=19.0, pickup_lng=181.0,
                dest_lat=19.1, dest_lng=72.1,
            )

    def test_driver_location_valid(self):
        p = DriverLocationPayload(
            driver_id=5,
            latitude=28.644,
            longitude=77.216,
            heading=90.0,
            speed_kmh=30.0,
            accuracy_m=5.0,
        )
        assert p.driver_id == 5
        assert p.heading == 90.0

    def test_driver_availability_payload(self):
        p = DriverAvailabilityPayload(
            driver_id=1,
            is_online=True,
            is_available=True,
        )
        assert p.is_online is True

    def test_notification_payload(self):
        p = NotificationRequestedPayload(
            recipient_role="user",
            recipient_id=42,
            notification_type="ride_update",
            title="Ride Accepted",
            body="Your driver is on the way!",
            data={"trip_id": 10},
        )
        assert p.recipient_role == "user"
        assert p.data["trip_id"] == 10


# ── State machine tests ───────────────────────────────────────────────────

class TestRideStateMachine:
    """Tests for the ride status state machine."""

    def test_valid_transitions(self):
        """All explicitly defined transitions should be valid."""
        assert validate_transition(RideStatus.REQUESTED, RideStatus.MATCHING) is True
        assert validate_transition(RideStatus.REQUESTED, RideStatus.CANCELLED) is True
        assert validate_transition(RideStatus.MATCHING, RideStatus.DRIVER_ASSIGNED) is True
        assert validate_transition(RideStatus.DRIVER_ASSIGNED, RideStatus.ACCEPTED) is True
        assert validate_transition(RideStatus.DRIVER_ASSIGNED, RideStatus.MATCHING) is True
        assert validate_transition(RideStatus.ACCEPTED, RideStatus.DRIVER_EN_ROUTE) is True
        assert validate_transition(RideStatus.IN_PROGRESS, RideStatus.COMPLETED) is True

    def test_invalid_transitions(self):
        """Invalid transitions should be rejected."""
        assert validate_transition(RideStatus.COMPLETED, RideStatus.REQUESTED) is False
        assert validate_transition(RideStatus.CANCELLED, RideStatus.MATCHING) is False
        assert validate_transition(RideStatus.REQUESTED, RideStatus.COMPLETED) is False
        assert validate_transition(RideStatus.IN_PROGRESS, RideStatus.CANCELLED) is False

    def test_terminal_states_have_no_transitions(self):
        """Terminal states (COMPLETED, CANCELLED) have no outgoing transitions."""
        assert VALID_TRANSITIONS[RideStatus.COMPLETED] == []
        assert VALID_TRANSITIONS[RideStatus.CANCELLED] == []

    def test_all_states_in_transition_map(self):
        """Every RideStatus should be present in VALID_TRANSITIONS."""
        for status in RideStatus:
            assert status in VALID_TRANSITIONS, (
                f"Missing transition entry for {status}"
            )


# ── DLQ tests ──────────────────────────────────────────────────────────────

class TestDLQEntry:
    """Tests for Dead Letter Queue entry."""

    def test_dlq_serialize_deserialize(self):
        entry = DLQEntry(
            original_topic="ridebooking.rides.v1",
            original_partition=3,
            original_offset=42,
            original_event={"event_type": "ride.requested"},
            error_message="Processing failed",
            error_type="ValueError",
            consumer_group="test-group",
        )

        raw = entry.serialize()
        assert isinstance(raw, bytes)

        restored = DLQEntry.deserialize(raw)
        assert restored.original_topic == "ridebooking.rides.v1"
        assert restored.original_offset == 42
        assert restored.error_message == "Processing failed"


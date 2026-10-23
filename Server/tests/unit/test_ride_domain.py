"""
Unit tests for ride state transitions (Bug #14: TripStatus inconsistency,
and future trip lifecycle state machine).
RED PHASE.
"""
import pytest


class TestTripStatusEnum:
    """Tests for TripStatus values consistency."""

    def test_dismiss_enum_value_matches_db_value(self):
        """Bug #14: TripStatus.dismiss must equal 'dismissed' not 'dismiss'."""
        from schemas.trip_request_schema import TripStatus
        assert TripStatus.dismissed.value == "dismissed"

    def test_all_expected_statuses_exist(self):
        from schemas.trip_request_schema import TripStatus
        expected = {"pending", "accepted", "rejected", "completed", "dismissed", "cancelled"}
        actual = {s.value for s in TripStatus}
        assert expected == actual

    def test_pending_is_default_readable_value(self):
        from schemas.trip_request_schema import TripStatus
        assert TripStatus.pending.value == "pending"

    def test_accepted_value(self):
        from schemas.trip_request_schema import TripStatus
        assert TripStatus.accepted.value == "accepted"

    def test_rejected_value(self):
        from schemas.trip_request_schema import TripStatus
        assert TripStatus.rejected.value == "rejected"


class TestTripRequestResponseSchema:
    """Tests for Bug #5: TripRequestResponse missing 'status' field."""

    def test_response_schema_has_status_field(self):
        from schemas.trip_request_schema import TripRequestResponse
        fields = TripRequestResponse.model_fields
        assert "status" in fields, "TripRequestResponse must have a 'status' field"

    def test_response_schema_has_trip_id_field(self):
        from schemas.trip_request_schema import TripRequestResponse
        assert "trip_id" in TripRequestResponse.model_fields

    def test_response_schema_has_message_field(self):
        from schemas.trip_request_schema import TripRequestResponse
        assert "message" in TripRequestResponse.model_fields

    def test_response_schema_instantiation(self):
        from schemas.trip_request_schema import TripRequestResponse
        r = TripRequestResponse(status=True, trip_id=1, message="OK")
        assert r.status is True
        assert r.trip_id == 1
        assert r.message == "OK"


class TestCoordinateValidation:
    """Tests for coordinate range validation on location inputs."""

    def test_valid_coordinates_accepted(self):
        from schemas.DriverLocation import LocationGenerate
        loc = LocationGenerate(latitude=28.6, longitude=77.2)
        assert loc.latitude == 28.6
        assert loc.longitude == 77.2

    def test_latitude_above_90_rejected(self):
        from schemas.DriverLocation import LocationGenerate
        with pytest.raises(Exception):
            LocationGenerate(latitude=91.0, longitude=77.2)

    def test_latitude_below_minus_90_rejected(self):
        from schemas.DriverLocation import LocationGenerate
        with pytest.raises(Exception):
            LocationGenerate(latitude=-91.0, longitude=77.2)

    def test_longitude_above_180_rejected(self):
        from schemas.DriverLocation import LocationGenerate
        with pytest.raises(Exception):
            LocationGenerate(latitude=28.6, longitude=181.0)

    def test_longitude_below_minus_180_rejected(self):
        from schemas.DriverLocation import LocationGenerate
        with pytest.raises(Exception):
            LocationGenerate(latitude=28.6, longitude=-181.0)


class TestDistanceCalculation:
    """Tests for the Haversine distance calculation utility."""

    def test_same_location_returns_zero(self):
        from utils.distance import calculate_distance
        d = calculate_distance(28.6, 77.2, 28.6, 77.2)
        assert abs(d) < 0.001

    def test_known_distance_mumbai_delhi(self):
        """Mumbai to Delhi is approximately 1150 km."""
        from utils.distance import calculate_distance
        d = calculate_distance(19.076, 72.877, 28.704, 77.102)
        assert 1100 < d < 1200

    def test_returns_float(self):
        from utils.distance import calculate_distance
        d = calculate_distance(0, 0, 1, 1)
        assert isinstance(d, float)

    def test_distance_is_symmetric(self):
        """Distance A→B == Distance B→A."""
        from utils.distance import calculate_distance
        d1 = calculate_distance(19.076, 72.877, 28.704, 77.102)
        d2 = calculate_distance(28.704, 77.102, 19.076, 72.877)
        assert abs(d1 - d2) < 0.001

    def test_invalid_latitude_type_raises(self):
        from utils.distance import calculate_distance
        with pytest.raises((TypeError, ValueError)):
            calculate_distance("bad", 77.2, 28.6, 77.2)

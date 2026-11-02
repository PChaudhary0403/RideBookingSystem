"""
Driver matching service.

Finds nearby available drivers using a Redis geospatial index for O(log N)
lookups, with an automatic fallback to a PostgreSQL O(N) scan when Redis
is unavailable.  Assigns the closest available driver to a ride request
atomically using ``SELECT FOR UPDATE``.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from DynamicDB.models.triprequest import TripRequest
from DynamicDB.models.active_riders import ActiveDriver
from DynamicDB.models.Driver_Location import DriverLocation
from kafka.redis_client import RedisGeo
from kafka.schemas import (
    EventEnvelope,
    EventType,
    RideDriverAssignedPayload,
)
from kafka.outbox.repository import OutboxRepository
from kafka.topics import Topics

logger = logging.getLogger(__name__)


# ── Haversine helper ───────────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometres.

    Args:
        lat1: Latitude of point 1 (decimal degrees).
        lon1: Longitude of point 1 (decimal degrees).
        lat2: Latitude of point 2 (decimal degrees).
        lon2: Longitude of point 2 (decimal degrees).

    Returns:
        Distance in kilometres.
    """
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class DriverMatchingService:
    """Finds nearby available drivers using Redis geospatial index with PostgreSQL fallback."""

    def __init__(self) -> None:
        self.max_radius_km: float = 10.0
        self.initial_radius_km: float = 3.0
        self.max_candidates: int = 10
        self.radius_expansion_steps: List[float] = [3.0, 5.0, 7.0, 10.0]

    # ── 1. Find nearby drivers ─────────────────────────────────────────────

    def find_nearby_drivers(
        self,
        db: Session,
        pickup_lat: float,
        pickup_lng: float,
        radius_km: float = 5.0,
        max_count: int = 10,
    ) -> List[Dict]:
        """Find available drivers near a pickup location.

        Tries the Redis GEO index first for O(log N) performance.  If
        Redis is unavailable or returns no results, falls back to a
        PostgreSQL scan using the haversine formula.

        Args:
            db: Active SQLAlchemy session.
            pickup_lat: Pickup latitude.
            pickup_lng: Pickup longitude.
            radius_km: Search radius in kilometres.
            max_count: Maximum number of driver candidates to return.

        Returns:
            A list of dicts, each containing ``driver_id``,
            ``distance_km``, ``latitude``, and ``longitude``, sorted by
            distance ascending.
        """
        # Try Redis first
        drivers = self._find_via_redis(pickup_lat, pickup_lng, radius_km, max_count)
        if drivers:
            # Filter to only available drivers via DB check
            drivers = self._filter_available(db, drivers)
            if drivers:
                return drivers[:max_count]

        # Fallback to PostgreSQL
        logger.debug(
            "Redis unavailable or returned no results; falling back to PostgreSQL scan."
        )
        return self._find_via_postgres(db, pickup_lat, pickup_lng, radius_km, max_count)

    def _find_via_redis(
        self,
        lat: float,
        lng: float,
        radius_km: float,
        max_count: int,
    ) -> List[Dict]:
        """Attempt driver lookup via Redis GEO commands.

        Args:
            lat: Latitude of the search centre.
            lng: Longitude of the search centre.
            radius_km: Search radius in kilometres.
            max_count: Maximum results to fetch.

        Returns:
            A list of driver dicts, or an empty list on error.
        """
        try:
            geo = RedisGeo()
            if not geo.is_available():
                return []
            return geo.find_nearby_drivers(
                lat=lat, lng=lng, radius_km=radius_km, count=max_count
            )
        except Exception as exc:
            logger.warning("Redis geo lookup failed: %s", exc)
            return []

    def _filter_available(
        self,
        db: Session,
        candidates: List[Dict],
    ) -> List[Dict]:
        """Remove candidates who are not online + available in the DB.

        Args:
            db: Active SQLAlchemy session.
            candidates: List of driver dicts from Redis.

        Returns:
            Filtered list containing only available drivers.
        """
        driver_ids = [c["driver_id"] for c in candidates]
        available_ids = set(
            row.driver_id
            for row in db.query(ActiveDriver.driver_id)
            .filter(
                ActiveDriver.driver_id.in_(driver_ids),
                ActiveDriver.is_online.is_(True),
                ActiveDriver.is_available.is_(True),
            )
            .all()
        )
        return [c for c in candidates if c["driver_id"] in available_ids]

    def _find_via_postgres(
        self,
        db: Session,
        pickup_lat: float,
        pickup_lng: float,
        radius_km: float,
        max_count: int,
    ) -> List[Dict]:
        """O(N) PostgreSQL fallback using the haversine formula.

        Joins ``DriverLocation`` with ``ActiveDriver`` to find online,
        available drivers within the specified radius.

        Args:
            db: Active SQLAlchemy session.
            pickup_lat: Pickup latitude.
            pickup_lng: Pickup longitude.
            radius_km: Maximum distance in kilometres.
            max_count: Maximum results to return.

        Returns:
            A sorted list of driver dicts.
        """
        rows = (
            db.query(DriverLocation, ActiveDriver)
            .join(
                ActiveDriver,
                DriverLocation.driver_id == ActiveDriver.driver_id,
            )
            .filter(
                ActiveDriver.is_online.is_(True),
                ActiveDriver.is_available.is_(True),
            )
            .all()
        )

        candidates: List[Dict] = []
        for loc, _active in rows:
            dist = _haversine(pickup_lat, pickup_lng, loc.latitude, loc.longitude)
            if dist <= radius_km:
                candidates.append(
                    {
                        "driver_id": loc.driver_id,
                        "distance_km": round(dist, 2),
                        "latitude": loc.latitude,
                        "longitude": loc.longitude,
                    }
                )

        candidates.sort(key=lambda d: d["distance_km"])
        return candidates[:max_count]

    # ── 2. Assign best driver ──────────────────────────────────────────────

    def assign_best_driver(
        self,
        db: Session,
        trip_req_id: int,
        pickup_lat: float,
        pickup_lng: float,
    ) -> Optional[Tuple[int, float]]:
        """Find and assign the closest available driver to a ride request.

        Searches with an expanding radius until a candidate is found or
        the maximum radius is reached.  The selected driver's row is
        locked with ``SELECT FOR UPDATE`` to prevent concurrent
        assignment.

        Args:
            db: Active SQLAlchemy session.
            trip_req_id: ID of the trip request to assign.
            pickup_lat: Pickup latitude.
            pickup_lng: Pickup longitude.

        Returns:
            A tuple of ``(driver_id, distance_km)`` on success, or
            ``None`` if no driver is available within the maximum radius.
        """
        for radius in self.radius_expansion_steps:
            candidates = self.find_nearby_drivers(
                db, pickup_lat, pickup_lng, radius_km=radius, max_count=self.max_candidates
            )
            if not candidates:
                logger.debug(
                    "No drivers found within %.1f km for trip %d, expanding radius.",
                    radius,
                    trip_req_id,
                )
                continue

            # Try to lock and assign the closest candidate
            for candidate in candidates:
                driver_id = candidate["driver_id"]
                distance_km = candidate["distance_km"]

                # Lock the ActiveDriver row
                try:
                    active_driver = (
                        db.query(ActiveDriver)
                        .filter(
                            ActiveDriver.driver_id == driver_id,
                            ActiveDriver.is_online.is_(True),
                            ActiveDriver.is_available.is_(True),
                        )
                        .with_for_update()
                        .first()
                    )
                except Exception:
                    # SQLite fallback (no FOR UPDATE support)
                    active_driver = (
                        db.query(ActiveDriver)
                        .filter(
                            ActiveDriver.driver_id == driver_id,
                            ActiveDriver.is_online.is_(True),
                            ActiveDriver.is_available.is_(True),
                        )
                        .first()
                    )

                if active_driver is None:
                    # Driver was grabbed by another request; try next
                    continue

                # Lock the trip request
                try:
                    trip = (
                        db.query(TripRequest)
                        .filter(TripRequest.id == trip_req_id)
                        .with_for_update()
                        .first()
                    )
                except Exception:
                    trip = (
                        db.query(TripRequest)
                        .filter(TripRequest.id == trip_req_id)
                        .first()
                    )

                if trip is None:
                    raise ValueError(f"TripRequest {trip_req_id} not found")

                # Update trip
                trip.driver_id = driver_id
                trip.status = "assigned"
                trip.updated_at = datetime.now(timezone.utc)

                # Mark driver unavailable
                active_driver.is_available = False

                # Emit outbox event
                envelope = EventEnvelope.create(
                    event_type=EventType.RIDE_DRIVER_ASSIGNED,
                    aggregate_type="ride",
                    aggregate_id=str(trip.id),
                    payload=RideDriverAssignedPayload(
                        ride_id=trip.id,
                        driver_id=driver_id,
                    ),
                    source="driver-matching-service",
                )
                OutboxRepository.create_event_from_envelope(
                    db, Topics.RIDES, envelope
                )

                db.commit()
                logger.info(
                    "Driver assigned: trip_id=%d driver=%d distance=%.2f km",
                    trip.id,
                    driver_id,
                    distance_km,
                )
                return (driver_id, distance_km)

        logger.warning(
            "No available driver found for trip %d within %.1f km.",
            trip_req_id,
            self.max_radius_km,
        )
        return None

    # ── 3. Release driver ──────────────────────────────────────────────────

    @staticmethod
    def release_driver(db: Session, driver_id: int) -> None:
        """Mark a driver as available again.

        Args:
            db: Active SQLAlchemy session.
            driver_id: ID of the driver to release.
        """
        driver = (
            db.query(ActiveDriver)
            .filter(ActiveDriver.driver_id == driver_id)
            .first()
        )
        if driver:
            driver.is_available = True
            db.commit()
            logger.info("Driver released: driver_id=%d", driver_id)
        else:
            logger.warning(
                "Cannot release driver %d: ActiveDriver record not found.",
                driver_id,
            )

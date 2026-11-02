"""
Redis client utilities for the Ride Booking System.

Provides a connection pool, geospatial operations for driver discovery,
and rate-limiting primitives.

Usage::

    from kafka.redis_client import get_redis, RedisGeo

    redis = get_redis()
    geo = RedisGeo(redis)
    geo.update_driver_location(driver_id=7, lat=19.076, lng=72.877)
    nearby = geo.find_nearby_drivers(lat=19.1, lng=72.9, radius_km=5)
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple

import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

from kafka.config import RedisConfig, get_redis_config

logger = logging.getLogger(__name__)

# Module-level singleton
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def get_redis(config: RedisConfig | None = None) -> redis.Redis:
    """Return a shared Redis client backed by a connection pool.

    Thread-safe; the pool is created on first call and reused.

    Args:
        config: Optional RedisConfig; used only on first initialization.

    Returns:
        A ``redis.Redis`` instance with a shared connection pool.
    """
    global _redis_pool, _redis_client

    if _redis_client is not None:
        return _redis_client

    cfg = config or get_redis_config()

    _redis_pool = redis.ConnectionPool(
        host=cfg.host,
        port=cfg.port,
        db=cfg.db,
        password=cfg.password,
        max_connections=cfg.max_connections,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )

    _redis_client = redis.Redis(connection_pool=_redis_pool)

    # Test connection
    try:
        _redis_client.ping()
        logger.info(
            "Redis connected: host=%s port=%d db=%d",
            cfg.host,
            cfg.port,
            cfg.db,
        )
    except RedisError as exc:
        logger.warning(
            "Redis connection test failed (host=%s): %s. "
            "Geospatial features will fall back to PostgreSQL.",
            cfg.host,
            exc,
        )

    return _redis_client


def close_redis() -> None:
    """Close the shared Redis connection pool."""
    global _redis_pool, _redis_client
    if _redis_pool is not None:
        _redis_pool.disconnect()
        _redis_pool = None
        _redis_client = None
        logger.info("Redis connection pool closed.")


class RedisGeo:
    """Geospatial operations for driver location tracking.

    Uses Redis GEO commands (GEOADD, GEORADIUS, GEOPOS) for O(log(N))
    nearest-driver lookups, replacing the O(N) Python scan.
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        geo_key: str = "drivers:active",
    ) -> None:
        self._redis = redis_client or get_redis()
        self._geo_key = geo_key

    def update_driver_location(
        self,
        driver_id: int,
        lat: float,
        lng: float,
    ) -> bool:
        """Add or update a driver's location in the geospatial index.

        Args:
            driver_id: The driver's ID.
            lat: Latitude in decimal degrees.
            lng: Longitude in decimal degrees.

        Returns:
            True if the update succeeded, False on Redis error.
        """
        try:
            # GEOADD key longitude latitude member
            self._redis.geoadd(self._geo_key, (lng, lat, str(driver_id)))
            return True
        except RedisError as exc:
            logger.error(
                "Redis GEOADD failed for driver %d: %s",
                driver_id,
                exc,
            )
            return False

    def remove_driver(self, driver_id: int) -> bool:
        """Remove a driver from the geospatial index (e.g., on logout).

        Args:
            driver_id: The driver's ID.

        Returns:
            True if removed, False on error.
        """
        try:
            self._redis.zrem(self._geo_key, str(driver_id))
            return True
        except RedisError as exc:
            logger.error(
                "Redis ZREM failed for driver %d: %s",
                driver_id,
                exc,
            )
            return False

    def find_nearby_drivers(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0,
        count: int = 20,
    ) -> List[Dict]:
        """Find drivers within a radius of the given coordinates.

        Args:
            lat: Latitude of the search center.
            lng: Longitude of the search center.
            radius_km: Search radius in kilometers.
            count: Maximum number of results.

        Returns:
            A list of dicts: ``{"driver_id": int, "distance_km": float,
            "latitude": float, "longitude": float}``.
            Returns an empty list on Redis errors (fallback to PostgreSQL).
        """
        try:
            results = self._redis.georadius(
                self._geo_key,
                longitude=lng,
                latitude=lat,
                radius=radius_km,
                unit="km",
                withdist=True,
                withcoord=True,
                count=count,
                sort="ASC",  # nearest first
            )

            drivers = []
            for item in results:
                member = item[0]
                distance = float(item[1])
                coord = item[2]  # (lng, lat)
                drivers.append({
                    "driver_id": int(member),
                    "distance_km": round(distance, 2),
                    "longitude": float(coord[0]),
                    "latitude": float(coord[1]),
                })

            return drivers

        except RedisError as exc:
            logger.error(
                "Redis GEORADIUS failed (lat=%.4f, lng=%.4f, radius=%.1f km): %s",
                lat,
                lng,
                radius_km,
                exc,
            )
            return []

    def get_driver_position(
        self,
        driver_id: int,
    ) -> Optional[Tuple[float, float]]:
        """Get a single driver's current position.

        Args:
            driver_id: The driver's ID.

        Returns:
            A tuple of (latitude, longitude) or None if not found.
        """
        try:
            positions = self._redis.geopos(self._geo_key, str(driver_id))
            if positions and positions[0] is not None:
                lng, lat = positions[0]
                return (float(lat), float(lng))
            return None
        except RedisError as exc:
            logger.error(
                "Redis GEOPOS failed for driver %d: %s",
                driver_id,
                exc,
            )
            return None

    def get_active_driver_count(self) -> int:
        """Return the number of drivers in the geospatial index.

        Returns:
            Number of active drivers, or 0 on error.
        """
        try:
            return self._redis.zcard(self._geo_key)
        except RedisError:
            return 0

    def prune_stale_drivers(
        self,
        stale_driver_ids: List[int],
    ) -> int:
        """Remove drivers whose location data is stale.

        This is called by a background task that compares
        ``driver_locations.updated_at`` against a TTL threshold.

        Args:
            stale_driver_ids: List of driver IDs to remove.

        Returns:
            Number of drivers removed.
        """
        if not stale_driver_ids:
            return 0

        try:
            members = [str(did) for did in stale_driver_ids]
            removed = self._redis.zrem(self._geo_key, *members)
            logger.info(
                "Pruned %d stale drivers from geo index.",
                removed,
            )
            return removed
        except RedisError as exc:
            logger.error("Failed to prune stale drivers: %s", exc)
            return 0

    def is_available(self) -> bool:
        """Check if Redis is reachable.

        Returns:
            True if Redis responds to PING, False otherwise.
        """
        try:
            return self._redis.ping()
        except (RedisError, RedisConnectionError):
            return False

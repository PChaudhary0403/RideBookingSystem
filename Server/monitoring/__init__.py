"""
Prometheus metrics for the Ride Booking System.

Exposes application metrics via a ``/metrics`` endpoint compatible
with Prometheus scraping.  Covers:

- Kafka producer and consumer stats
- Ride lifecycle durations
- Driver matching performance
- Rate limit violations
- API request latency
- Outbox queue depth

Usage::

    from monitoring.metrics import (
        RIDE_REQUESTS_TOTAL,
        DRIVER_MATCH_DURATION,
        track_request_latency,
    )

    RIDE_REQUESTS_TOTAL.inc()
"""

from __future__ import annotations

import time
import logging
from functools import wraps
from typing import Callable

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import APIRouter, Response

logger = logging.getLogger(__name__)


# ── Application info ───────────────────────────────────────────────────────

APP_INFO = Info(
    "ridebooking_app",
    "Ride Booking System application info",
)
APP_INFO.info({
    "version": "2.0.0",
    "architecture": "event-driven",
    "messaging": "kafka",
})


# ── Ride metrics ───────────────────────────────────────────────────────────

RIDE_REQUESTS_TOTAL = Counter(
    "ridebooking_ride_requests_total",
    "Total number of ride requests created",
    ["status"],  # success, error
)

RIDE_LIFECYCLE_TRANSITIONS = Counter(
    "ridebooking_ride_transitions_total",
    "Total ride status transitions",
    ["from_status", "to_status"],
)

RIDE_ASSIGNMENT_DURATION = Histogram(
    "ridebooking_ride_assignment_duration_seconds",
    "Time taken to assign a driver to a ride",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

ACTIVE_RIDES = Gauge(
    "ridebooking_active_rides",
    "Number of currently active rides",
)


# ── Driver metrics ─────────────────────────────────────────────────────────

DRIVER_MATCH_ATTEMPTS = Counter(
    "ridebooking_driver_match_attempts_total",
    "Total driver matching attempts",
    ["result"],  # success, no_drivers, error
)

DRIVER_MATCH_DURATION = Histogram(
    "ridebooking_driver_match_duration_seconds",
    "Time taken to find a matching driver",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

DRIVERS_ONLINE = Gauge(
    "ridebooking_drivers_online",
    "Number of drivers currently online",
)

DRIVER_LOCATION_UPDATES = Counter(
    "ridebooking_driver_location_updates_total",
    "Total driver location updates processed",
)


# ── Kafka metrics ──────────────────────────────────────────────────────────

KAFKA_MESSAGES_PRODUCED = Counter(
    "ridebooking_kafka_messages_produced_total",
    "Total messages produced to Kafka",
    ["topic", "status"],  # success, error
)

KAFKA_MESSAGES_CONSUMED = Counter(
    "ridebooking_kafka_messages_consumed_total",
    "Total messages consumed from Kafka",
    ["consumer_group", "status"],  # processed, failed, duplicate, dlq
)

KAFKA_CONSUMER_LAG = Gauge(
    "ridebooking_kafka_consumer_lag",
    "Consumer group lag (messages behind)",
    ["consumer_group"],
)

KAFKA_CONSUMER_PROCESSING_DURATION = Histogram(
    "ridebooking_kafka_consumer_processing_seconds",
    "Time taken to process a Kafka message",
    ["consumer_group", "event_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)


# ── Outbox metrics ─────────────────────────────────────────────────────────

OUTBOX_PENDING_GAUGE = Gauge(
    "ridebooking_outbox_pending_events",
    "Number of pending events in the outbox table",
)

OUTBOX_PUBLISHED_TOTAL = Counter(
    "ridebooking_outbox_published_total",
    "Total outbox events successfully published to Kafka",
)

OUTBOX_FAILED_TOTAL = Counter(
    "ridebooking_outbox_failed_total",
    "Total outbox events that exceeded retry limits",
)


# ── Rate limiting metrics ─────────────────────────────────────────────────

RATE_LIMIT_CHECKS = Counter(
    "ridebooking_rate_limit_checks_total",
    "Total rate limit checks performed",
    ["limit_type", "result"],  # allowed, rejected
)


# ── API metrics ────────────────────────────────────────────────────────────

API_REQUEST_DURATION = Histogram(
    "ridebooking_api_request_duration_seconds",
    "API request latency",
    ["method", "endpoint", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

API_REQUESTS_TOTAL = Counter(
    "ridebooking_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)


# ── Database metrics ───────────────────────────────────────────────────────

DB_CONNECTIONS_ACTIVE = Gauge(
    "ridebooking_db_connections_active",
    "Number of active database connections",
)


# ── Prometheus endpoint ───────────────────────────────────────────────────

metrics_router = APIRouter(tags=["monitoring"])


@metrics_router.get("/metrics")
def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ── Utility decorators ────────────────────────────────────────────────────

def track_request_latency(method: str, endpoint: str) -> Callable:
    """Decorator to track API request latency.

    Usage::

        @router.post("/ride-request/")
        @track_request_latency("POST", "/ride-request/")
        async def create_request(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                status = "200"
                return result
            except Exception as exc:
                status = "500"
                raise
            finally:
                duration = time.monotonic() - start
                API_REQUEST_DURATION.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status,
                ).observe(duration)
                API_REQUESTS_TOTAL.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=status,
                ).inc()

        return wrapper
    return decorator


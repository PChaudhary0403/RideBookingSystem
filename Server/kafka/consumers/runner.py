"""
Consumer runner — starts all Kafka consumers in daemon threads.

This module provides two usage modes:

1. **Standalone process** (separate from the FastAPI server)::

       python -m kafka.consumers.runner

2. **Integrated** (started from the FastAPI lifespan)::

       from kafka.consumers.runner import start_consumers, stop_consumers

       start_consumers()   # non-blocking — spawns daemon threads
       stop_consumers()    # signal all consumers to stop

Each consumer runs in its own daemon thread.  The base consumer
class handles retries, DLQ, and offset management.
"""

from __future__ import annotations

import logging
import signal
import sys
import threading
from typing import List

from kafka.consumer import BaseKafkaConsumer
from kafka.consumers.ride_consumer import RideLifecycleConsumer
from kafka.consumers.driver_consumer import DriverLocationConsumer
from kafka.consumers.notification_consumer import NotificationConsumer

logger = logging.getLogger(__name__)

_consumers: List[BaseKafkaConsumer] = []
_threads: List[threading.Thread] = []


def start_consumers() -> None:
    """Start all Kafka consumer threads.

    Each consumer runs in a daemon thread so the process exits
    cleanly when the main thread terminates.
    """
    global _consumers, _threads

    if _consumers:
        logger.warning("Consumers already started, skipping.")
        return

    consumer_classes = [
        RideLifecycleConsumer,
        DriverLocationConsumer,
        NotificationConsumer,
    ]

    for cls in consumer_classes:
        consumer = cls()
        thread = threading.Thread(
            target=consumer.start,
            daemon=True,
            name=f"consumer-{consumer._group_id}",
        )
        thread.start()
        _consumers.append(consumer)
        _threads.append(thread)

    logger.info(
        "Started %d consumer thread(s): %s",
        len(_threads),
        [c._group_id for c in _consumers],
    )


def stop_consumers() -> None:
    """Signal all consumers to stop and wait for threads to exit."""
    global _consumers, _threads

    if not _consumers:
        return

    logger.info("Stopping %d consumer(s)...", len(_consumers))

    for consumer in _consumers:
        try:
            consumer.stop()
        except Exception as exc:
            logger.error(
                "Error stopping consumer '%s': %s",
                consumer._group_id,
                exc,
            )

    for thread in _threads:
        thread.join(timeout=10)
        if thread.is_alive():
            logger.warning(
                "Consumer thread '%s' did not stop within timeout.",
                thread.name,
            )

    logger.info("All consumers stopped.")
    _consumers.clear()
    _threads.clear()


def _signal_handler(sig, frame) -> None:
    """Graceful shutdown on SIGINT/SIGTERM."""
    logger.info("Shutdown signal received (signal=%s).", sig)
    stop_consumers()
    sys.exit(0)


if __name__ == "__main__":
    # Standalone runner mode
    from logging_config import setup_logging

    setup_logging()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    logger.info("Starting Kafka consumer runner (standalone mode)...")
    start_consumers()

    # Keep the main thread alive while daemon threads run
    try:
        for thread in _threads:
            thread.join()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
        stop_consumers()


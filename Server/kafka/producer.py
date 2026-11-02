"""
Kafka producer with batching, compression, idempotency, and metrics.

Provides a singleton ``KafkaEventProducer`` that wraps the confluent-kafka
``Producer``.  It handles serialization, delivery callbacks, graceful
shutdown, and structured error reporting.

Usage::

    from kafka.producer import get_producer

    producer = get_producer()
    producer.publish(
        topic="ridebooking.rides.v1",
        key="ride_123",
        event=some_event_envelope,
    )
    # At shutdown:
    producer.flush()
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable, Dict, Optional

from confluent_kafka import KafkaError, KafkaException, Producer

from kafka.config import KafkaConfig, get_kafka_config
from kafka.schemas import EventEnvelope

logger = logging.getLogger(__name__)

# Module-level singleton
_producer_instance: Optional["KafkaEventProducer"] = None
_producer_lock = threading.Lock()


class ProducerMetrics:
    """Simple thread-safe counters for producer observability.

    These are intended to be exported to Prometheus in the monitoring module.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.messages_sent: int = 0
        self.messages_failed: int = 0
        self.bytes_sent: int = 0
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[float] = None

    def record_success(self, size: int) -> None:
        with self._lock:
            self.messages_sent += 1
            self.bytes_sent += size

    def record_failure(self, error: str) -> None:
        with self._lock:
            self.messages_failed += 1
            self.last_error = error
            self.last_error_time = time.time()

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            return {
                "messages_sent": self.messages_sent,
                "messages_failed": self.messages_failed,
                "bytes_sent": self.bytes_sent,
                "last_error": self.last_error,
                "last_error_time": self.last_error_time,
            }


class KafkaEventProducer:
    """Thread-safe Kafka producer with delivery tracking.

    Wraps ``confluent_kafka.Producer`` with:
    - Automatic serialization of ``EventEnvelope``
    - Delivery callbacks for success/failure logging
    - Metrics collection
    - Graceful ``flush()`` and ``close()``

    This class is designed to be used as a singleton via ``get_producer()``.
    """

    def __init__(self, config: KafkaConfig | None = None) -> None:
        self._config = config or get_kafka_config()
        self.metrics = ProducerMetrics()
        self._closed = False

        producer_conf: Dict[str, object] = {
            "bootstrap.servers": self._config.bootstrap_servers,
            "acks": self._config.producer_acks,
            "retries": self._config.producer_retries,
            "batch.size": self._config.producer_batch_size,
            "linger.ms": self._config.producer_linger_ms,
            "compression.type": self._config.producer_compression_type,
            "buffer.memory": self._config.producer_buffer_memory,
            "max.block.ms": self._config.producer_max_block_ms,
            "delivery.timeout.ms": self._config.producer_delivery_timeout_ms,
            "enable.idempotence": self._config.producer_enable_idempotence,
        }

        # Optional SASL authentication
        if self._config.security_protocol != "PLAINTEXT":
            producer_conf["security.protocol"] = self._config.security_protocol
        if self._config.sasl_mechanism:
            producer_conf["sasl.mechanism"] = self._config.sasl_mechanism
        if self._config.sasl_username:
            producer_conf["sasl.username"] = self._config.sasl_username
        if self._config.sasl_password:
            producer_conf["sasl.password"] = self._config.sasl_password

        self._producer = Producer(producer_conf)
        logger.info(
            "KafkaEventProducer initialized (servers=%s, acks=%s, idempotence=%s)",
            self._config.bootstrap_servers,
            self._config.producer_acks,
            self._config.producer_enable_idempotence,
        )

    def _delivery_callback(self, err: Optional[KafkaError], msg) -> None:
        """Called once per message when Kafka confirms or rejects delivery."""
        if err is not None:
            self.metrics.record_failure(str(err))
            logger.error(
                "Kafka delivery failed: topic=%s partition=%s error=%s",
                msg.topic(),
                msg.partition(),
                err,
            )
        else:
            self.metrics.record_success(len(msg.value()) if msg.value() else 0)
            logger.debug(
                "Kafka delivery confirmed: topic=%s partition=%s offset=%s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    def publish(
        self,
        topic: str,
        key: str,
        event: EventEnvelope,
        on_delivery: Optional[Callable] = None,
    ) -> None:
        """Publish an event envelope to a Kafka topic.

        The message is enqueued in the internal buffer and sent
        asynchronously.  Call ``flush()`` to block until all buffered
        messages are delivered.

        Args:
            topic: Kafka topic name.
            key: Partition key (e.g. ride_id, driver_id as string).
            event: The EventEnvelope to serialize and send.
            on_delivery: Optional custom delivery callback.

        Raises:
            RuntimeError: If the producer has been closed.
            BufferError: If the internal buffer is full (backpressure).
        """
        if self._closed:
            raise RuntimeError("Cannot publish: producer has been closed.")

        value = event.serialize()
        key_bytes = key.encode("utf-8")

        try:
            self._producer.produce(
                topic=topic,
                key=key_bytes,
                value=value,
                callback=on_delivery or self._delivery_callback,
            )
            # Trigger delivery report callbacks from previous sends
            self._producer.poll(0)
        except BufferError:
            logger.warning(
                "Producer buffer full (topic=%s, key=%s). "
                "Flushing and retrying once.",
                topic,
                key,
            )
            self._producer.flush(timeout=5)
            # Retry once after flush
            self._producer.produce(
                topic=topic,
                key=key_bytes,
                value=value,
                callback=on_delivery or self._delivery_callback,
            )

    def publish_raw(
        self,
        topic: str,
        key: str,
        value: bytes,
        on_delivery: Optional[Callable] = None,
    ) -> None:
        """Publish raw bytes to a Kafka topic (used for DLQ entries).

        Args:
            topic: Kafka topic name.
            key: Partition key as string.
            value: Pre-serialized bytes.
            on_delivery: Optional delivery callback.
        """
        if self._closed:
            raise RuntimeError("Cannot publish: producer has been closed.")

        try:
            self._producer.produce(
                topic=topic,
                key=key.encode("utf-8"),
                value=value,
                callback=on_delivery or self._delivery_callback,
            )
            self._producer.poll(0)
        except BufferError:
            self._producer.flush(timeout=5)
            self._producer.produce(
                topic=topic,
                key=key.encode("utf-8"),
                value=value,
                callback=on_delivery or self._delivery_callback,
            )

    def flush(self, timeout: float = 10.0) -> int:
        """Flush all buffered messages, blocking until complete.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            Number of messages still in the queue (0 = all delivered).
        """
        remaining = self._producer.flush(timeout=timeout)
        if remaining > 0:
            logger.warning(
                "Producer flush timed out: %d messages still in queue.",
                remaining,
            )
        return remaining

    def poll(self, timeout: float = 0) -> int:
        """Poll for delivery callbacks without blocking.

        Args:
            timeout: Seconds to wait (0 = non-blocking).

        Returns:
            Number of callbacks processed.
        """
        return self._producer.poll(timeout)

    def close(self) -> None:
        """Flush remaining messages and mark the producer as closed."""
        if self._closed:
            return
        logger.info("Closing KafkaEventProducer, flushing remaining messages...")
        self.flush(timeout=15)
        self._closed = True
        logger.info(
            "KafkaEventProducer closed. Metrics: %s",
            self.metrics.snapshot(),
        )

    @property
    def is_healthy(self) -> bool:
        """Quick health check: producer is not closed."""
        return not self._closed


def get_producer(config: KafkaConfig | None = None) -> KafkaEventProducer:
    """Return the singleton KafkaEventProducer instance.

    Thread-safe; the producer is created on first call and reused.

    Args:
        config: Optional KafkaConfig; used only on first initialization.

    Returns:
        The shared KafkaEventProducer instance.
    """
    global _producer_instance
    if _producer_instance is None:
        with _producer_lock:
            if _producer_instance is None:
                _producer_instance = KafkaEventProducer(config)
    return _producer_instance


def close_producer() -> None:
    """Close the singleton producer (call at application shutdown)."""
    global _producer_instance
    with _producer_lock:
        if _producer_instance is not None:
            _producer_instance.close()
            _producer_instance = None

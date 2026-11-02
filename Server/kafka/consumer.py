"""
Base Kafka consumer with error handling, retries, DLQ, and graceful shutdown.

Provides ``BaseKafkaConsumer``, an abstract class that concrete consumers
extend by implementing ``handle_event()``.  The base class manages:

- Consumer group membership and rebalancing
- Manual offset commits (after processing)
- Exponential backoff with jitter on processing errors
- Dead Letter Queue publishing for poison messages
- Graceful shutdown via ``stop()``
- Structured logging

Usage::

    from kafka.consumer import BaseKafkaConsumer

    class MyConsumer(BaseKafkaConsumer):
        def handle_event(self, envelope):
            print(f"Got {envelope.event_type}")

    consumer = MyConsumer(
        group_id="my-consumer-group",
        topics=["ridebooking.rides.v1"],
    )
    consumer.start()   # blocking — run in a thread
"""

from __future__ import annotations

import abc
import logging
import random
import signal
import threading
import time
from typing import Dict, List, Optional, Set

from confluent_kafka import Consumer, KafkaError, KafkaException, TopicPartition

from kafka.config import KafkaConfig, get_kafka_config
from kafka.producer import get_producer
from kafka.schemas import DLQEntry, EventEnvelope
from kafka.topics import Topics

logger = logging.getLogger(__name__)


class ConsumerMetrics:
    """Thread-safe counters for consumer observability."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.messages_processed: int = 0
        self.messages_failed: int = 0
        self.messages_skipped_duplicate: int = 0
        self.messages_sent_to_dlq: int = 0
        self.last_processed_offset: Dict[str, int] = {}
        self.total_processing_time_ms: float = 0.0

    def record_processed(self, topic: str, partition: int, offset: int, duration_ms: float) -> None:
        with self._lock:
            self.messages_processed += 1
            self.total_processing_time_ms += duration_ms
            key = f"{topic}-{partition}"
            self.last_processed_offset[key] = offset

    def record_failed(self) -> None:
        with self._lock:
            self.messages_failed += 1

    def record_duplicate(self) -> None:
        with self._lock:
            self.messages_skipped_duplicate += 1

    def record_dlq(self) -> None:
        with self._lock:
            self.messages_sent_to_dlq += 1

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            avg_ms = (
                self.total_processing_time_ms / self.messages_processed
                if self.messages_processed > 0
                else 0.0
            )
            return {
                "messages_processed": self.messages_processed,
                "messages_failed": self.messages_failed,
                "messages_skipped_duplicate": self.messages_skipped_duplicate,
                "messages_sent_to_dlq": self.messages_sent_to_dlq,
                "avg_processing_time_ms": round(avg_ms, 2),
                "last_processed_offset": dict(self.last_processed_offset),
            }


class BaseKafkaConsumer(abc.ABC):
    """Abstract base class for Kafka event consumers.

    Subclasses must implement:
    - ``handle_event(envelope)`` — process a single deserialized event

    Optionally override:
    - ``get_handled_event_types()`` — filter to specific event types
    - ``on_startup()`` — hook called before the polling loop begins
    - ``on_shutdown()`` — hook called after the polling loop ends
    """

    # Retry configuration
    MAX_RETRIES: int = 5
    BASE_RETRY_DELAY: float = 1.0       # seconds
    MAX_RETRY_DELAY: float = 60.0       # seconds

    def __init__(
        self,
        group_id: str,
        topics: List[str],
        config: KafkaConfig | None = None,
    ) -> None:
        self._config = config or get_kafka_config()
        self._group_id = group_id
        self._topics = topics
        self._running = False
        self._consumer: Optional[Consumer] = None
        self.metrics = ConsumerMetrics()

        consumer_conf: Dict[str, object] = {
            "bootstrap.servers": self._config.bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": self._config.consumer_auto_offset_reset,
            "enable.auto.commit": self._config.consumer_enable_auto_commit,
            "max.poll.interval.ms": self._config.consumer_max_poll_interval_ms,
            "session.timeout.ms": self._config.consumer_session_timeout_ms,
        }

        # Optional SASL
        if self._config.security_protocol != "PLAINTEXT":
            consumer_conf["security.protocol"] = self._config.security_protocol
        if self._config.sasl_mechanism:
            consumer_conf["sasl.mechanism"] = self._config.sasl_mechanism
        if self._config.sasl_username:
            consumer_conf["sasl.username"] = self._config.sasl_username
        if self._config.sasl_password:
            consumer_conf["sasl.password"] = self._config.sasl_password

        self._consumer_conf = consumer_conf

    @abc.abstractmethod
    def handle_event(self, envelope: EventEnvelope) -> None:
        """Process a single event.  Must be implemented by subclasses.

        If this method raises an exception, the base class will retry
        with exponential backoff before sending the message to the DLQ.

        Args:
            envelope: The deserialized event envelope.
        """

    def get_handled_event_types(self) -> Optional[Set[str]]:
        """Return the set of event types this consumer handles.

        If ``None`` is returned, all event types are processed.
        Override this to filter and skip irrelevant events.

        Returns:
            A set of event type strings, or None for all.
        """
        return None

    def on_startup(self) -> None:
        """Hook called once before the polling loop begins."""

    def on_shutdown(self) -> None:
        """Hook called once after the polling loop ends."""

    def start(self) -> None:
        """Start the consumer polling loop (blocking).

        This method blocks the calling thread.  Run in a dedicated
        thread or process for concurrent consumers.
        """
        self._consumer = Consumer(self._consumer_conf)
        self._consumer.subscribe(self._topics)
        self._running = True

        logger.info(
            "Consumer '%s' starting: topics=%s",
            self._group_id,
            self._topics,
        )

        self.on_startup()

        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    self._handle_consumer_error(msg.error())
                    continue

                self._process_message(msg)

        except KeyboardInterrupt:
            logger.info("Consumer '%s' interrupted.", self._group_id)
        finally:
            self._shutdown()

    def stop(self) -> None:
        """Signal the consumer to stop gracefully after current poll."""
        logger.info("Consumer '%s' stop requested.", self._group_id)
        self._running = False

    def _shutdown(self) -> None:
        """Internal shutdown: commit offsets and close consumer."""
        logger.info(
            "Consumer '%s' shutting down. Metrics: %s",
            self._group_id,
            self.metrics.snapshot(),
        )
        try:
            self.on_shutdown()
        except Exception as exc:
            logger.error("Error in on_shutdown hook: %s", exc)

        if self._consumer:
            try:
                self._consumer.close()
            except Exception as exc:
                logger.error("Error closing consumer: %s", exc)

    def _handle_consumer_error(self, error: KafkaError) -> None:
        """Handle Kafka-level consumer errors."""
        if error.code() == KafkaError._PARTITION_EOF:
            # End of partition — normal, not an error
            logger.debug(
                "Reached end of partition: %s [%s]",
                error.name(),
                error,
            )
        elif error.code() == KafkaError._ALL_BROKERS_DOWN:
            logger.error(
                "All Kafka brokers are down. Consumer '%s' will retry...",
                self._group_id,
            )
            time.sleep(5)
        else:
            logger.error(
                "Consumer '%s' error: %s",
                self._group_id,
                error,
            )

    def _process_message(self, msg) -> None:
        """Deserialize, filter, and process a single Kafka message."""
        topic = msg.topic()
        partition = msg.partition()
        offset = msg.offset()

        # Deserialize envelope
        try:
            envelope = EventEnvelope.deserialize(msg.value())
        except Exception as exc:
            logger.error(
                "Failed to deserialize message (topic=%s, partition=%d, offset=%d): %s",
                topic, partition, offset, exc,
            )
            self._send_to_dlq(msg, str(exc), type(exc).__name__)
            self._commit_offset(msg)
            return

        # Filter by event type if the consumer specifies a subset
        handled_types = self.get_handled_event_types()
        if handled_types is not None and envelope.event_type not in handled_types:
            logger.debug(
                "Skipping event_type=%s (not in handled set) at offset=%d",
                envelope.event_type,
                offset,
            )
            self._commit_offset(msg)
            return

        # Process with retry
        self._process_with_retry(msg, envelope)

    def _process_with_retry(self, msg, envelope: EventEnvelope) -> None:
        """Attempt to handle an event with exponential backoff retries."""
        topic = msg.topic()
        partition = msg.partition()
        offset = msg.offset()

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                start = time.monotonic()
                self.handle_event(envelope)
                duration_ms = (time.monotonic() - start) * 1000

                self.metrics.record_processed(
                    topic, partition, offset, duration_ms,
                )
                self._commit_offset(msg)

                logger.debug(
                    "Processed event: type=%s id=%s offset=%d (%.1f ms)",
                    envelope.event_type,
                    envelope.event_id,
                    offset,
                    duration_ms,
                )
                return  # success

            except Exception as exc:
                self.metrics.record_failed()

                if attempt < self.MAX_RETRIES:
                    delay = self._backoff_delay(attempt)
                    logger.warning(
                        "Error processing event (attempt %d/%d, "
                        "retrying in %.1fs): type=%s id=%s error=%s",
                        attempt + 1,
                        self.MAX_RETRIES + 1,
                        delay,
                        envelope.event_type,
                        envelope.event_id,
                        exc,
                    )
                    time.sleep(delay)
                else:
                    # Exhausted retries — send to DLQ
                    logger.error(
                        "Exhausted retries for event: type=%s id=%s error=%s. "
                        "Sending to DLQ.",
                        envelope.event_type,
                        envelope.event_id,
                        exc,
                    )
                    self._send_to_dlq(msg, str(exc), type(exc).__name__)
                    self._commit_offset(msg)

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter.

        Formula: min(base * 4^attempt, max_delay) + random(0, delay/2)
        """
        delay = min(
            self.BASE_RETRY_DELAY * (4 ** attempt),
            self.MAX_RETRY_DELAY,
        )
        jitter = random.uniform(0, delay / 2)
        return delay + jitter

    def _commit_offset(self, msg) -> None:
        """Manually commit the offset for a processed message."""
        try:
            self._consumer.commit(message=msg, asynchronous=False)
        except Exception as exc:
            logger.error(
                "Failed to commit offset (topic=%s, partition=%d, offset=%d): %s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
                exc,
            )

    def _send_to_dlq(
        self,
        msg,
        error_message: str,
        error_type: str,
    ) -> None:
        """Publish a failed message to the Dead Letter Queue topic."""
        try:
            # Try to parse the original event for the DLQ entry
            try:
                original_event = EventEnvelope.deserialize(msg.value()).model_dump(
                    mode="json"
                )
            except Exception:
                # If deserialization fails, store raw as string
                original_event = {"raw": msg.value().decode("utf-8", errors="replace")}

            dlq_entry = DLQEntry(
                original_topic=msg.topic(),
                original_partition=msg.partition(),
                original_offset=msg.offset(),
                original_event=original_event,
                error_message=error_message,
                error_type=error_type,
                consumer_group=self._group_id,
            )

            producer = get_producer()
            producer.publish_raw(
                topic=Topics.DLQ,
                key=f"dlq-{msg.topic()}-{msg.partition()}-{msg.offset()}",
                value=dlq_entry.serialize(),
            )
            self.metrics.record_dlq()

            logger.info(
                "Sent failed event to DLQ: topic=%s offset=%d error=%s",
                msg.topic(),
                msg.offset(),
                error_type,
            )

        except Exception as exc:
            # DLQ publishing itself failed — log but don't crash
            logger.error(
                "CRITICAL: Failed to send to DLQ: %s "
                "(original: topic=%s offset=%d error=%s)",
                exc,
                msg.topic(),
                msg.offset(),
                error_message,
            )

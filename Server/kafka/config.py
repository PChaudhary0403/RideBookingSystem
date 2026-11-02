"""
Centralized Kafka and Redis configuration.

All Kafka/Redis settings are loaded from environment variables with sensible
defaults for local development.  Production deployments override via .env or
container environment.

Usage::

    from kafka.config import get_kafka_config, get_redis_config

    kafka_cfg = get_kafka_config()
    redis_cfg = get_redis_config()
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Kafka configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KafkaConfig:
    """Immutable Kafka connection and tuning parameters."""

    # Connection
    bootstrap_servers: str = "localhost:9092"
    security_protocol: str = "PLAINTEXT"          # PLAINTEXT | SASL_SSL
    sasl_mechanism: Optional[str] = None          # SCRAM-SHA-256 | SCRAM-SHA-512
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    # Producer tuning
    producer_acks: str = "all"                    # all = wait for ISR
    producer_retries: int = 3
    producer_batch_size: int = 32_768             # 32 KB
    producer_linger_ms: int = 50                  # ms to wait for batching
    producer_compression_type: str = "lz4"
    producer_buffer_memory: int = 67_108_864      # 64 MB
    producer_max_block_ms: int = 5_000            # backpressure timeout
    producer_delivery_timeout_ms: int = 30_000
    producer_enable_idempotence: bool = True

    # Consumer tuning
    consumer_max_poll_records: int = 50
    consumer_max_poll_interval_ms: int = 300_000  # 5 min
    consumer_session_timeout_ms: int = 30_000
    consumer_auto_offset_reset: str = "earliest"
    consumer_enable_auto_commit: bool = False

    # Topic defaults
    default_num_partitions: int = 12
    default_replication_factor: int = 2           # 2 for dev, 3 for prod

    # Outbox publisher
    outbox_poll_interval_seconds: float = 0.5
    outbox_batch_size: int = 50
    outbox_max_retries: int = 5


def get_kafka_config() -> KafkaConfig:
    """Build KafkaConfig from environment variables.

    Every parameter can be overridden with a ``KAFKA_`` prefixed env var.
    For example ``KAFKA_BOOTSTRAP_SERVERS=broker1:9092,broker2:9092``.
    """
    return KafkaConfig(
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        ),
        security_protocol=os.getenv(
            "KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"
        ),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
        producer_acks=os.getenv("KAFKA_PRODUCER_ACKS", "all"),
        producer_retries=int(os.getenv("KAFKA_PRODUCER_RETRIES", "3")),
        producer_batch_size=int(
            os.getenv("KAFKA_PRODUCER_BATCH_SIZE", "32768")
        ),
        producer_linger_ms=int(
            os.getenv("KAFKA_PRODUCER_LINGER_MS", "50")
        ),
        producer_compression_type=os.getenv(
            "KAFKA_PRODUCER_COMPRESSION", "lz4"
        ),
        producer_buffer_memory=int(
            os.getenv("KAFKA_PRODUCER_BUFFER_MEMORY", "67108864")
        ),
        producer_max_block_ms=int(
            os.getenv("KAFKA_PRODUCER_MAX_BLOCK_MS", "5000")
        ),
        producer_delivery_timeout_ms=int(
            os.getenv("KAFKA_PRODUCER_DELIVERY_TIMEOUT_MS", "30000")
        ),
        producer_enable_idempotence=os.getenv(
            "KAFKA_PRODUCER_ENABLE_IDEMPOTENCE", "true"
        ).lower() == "true",
        consumer_max_poll_records=int(
            os.getenv("KAFKA_CONSUMER_MAX_POLL_RECORDS", "50")
        ),
        consumer_max_poll_interval_ms=int(
            os.getenv("KAFKA_CONSUMER_MAX_POLL_INTERVAL_MS", "300000")
        ),
        consumer_session_timeout_ms=int(
            os.getenv("KAFKA_CONSUMER_SESSION_TIMEOUT_MS", "30000")
        ),
        consumer_auto_offset_reset=os.getenv(
            "KAFKA_CONSUMER_AUTO_OFFSET_RESET", "earliest"
        ),
        consumer_enable_auto_commit=os.getenv(
            "KAFKA_CONSUMER_ENABLE_AUTO_COMMIT", "false"
        ).lower() == "true",
        default_num_partitions=int(
            os.getenv("KAFKA_DEFAULT_NUM_PARTITIONS", "12")
        ),
        default_replication_factor=int(
            os.getenv("KAFKA_DEFAULT_REPLICATION_FACTOR", "2")
        ),
        outbox_poll_interval_seconds=float(
            os.getenv("KAFKA_OUTBOX_POLL_INTERVAL_SECONDS", "0.5")
        ),
        outbox_batch_size=int(
            os.getenv("KAFKA_OUTBOX_BATCH_SIZE", "50")
        ),
        outbox_max_retries=int(
            os.getenv("KAFKA_OUTBOX_MAX_RETRIES", "5")
        ),
    )


# ---------------------------------------------------------------------------
# Redis configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RedisConfig:
    """Immutable Redis connection parameters."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False

    # Connection pool
    max_connections: int = 20

    # Geospatial
    driver_geo_key: str = "drivers:active"
    driver_location_ttl_seconds: int = 120        # prune stale entries

    # Rate limiting
    rate_limit_prefix: str = "ratelimit:"

    @property
    def url(self) -> str:
        """Build a ``redis://`` connection URL."""
        scheme = "rediss" if self.ssl else "redis"
        auth = f":{self.password}@" if self.password else ""
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"


def get_redis_config() -> RedisConfig:
    """Build RedisConfig from environment variables."""
    return RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD"),
        ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
        driver_location_ttl_seconds=int(
            os.getenv("REDIS_DRIVER_LOCATION_TTL", "120")
        ),
    )

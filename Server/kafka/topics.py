"""
Kafka topic definitions and management utilities.

Defines all topic names, partition counts, and replication factors
in a single place.  Provides a ``create_topics()`` utility for
bootstrapping the Kafka cluster on first startup.

Usage::

    from kafka.topics import Topics, create_topics

    print(Topics.RIDES)          # "ridebooking.rides.v1"
    await create_topics()        # idempotent topic creation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

from confluent_kafka.admin import AdminClient, NewTopic

from kafka.config import KafkaConfig, get_kafka_config

logger = logging.getLogger(__name__)


# ── Topic name constants ──────────────────────────────────────────────────

class Topics:
    """Central registry of all Kafka topic names.

    Naming convention: ``ridebooking.{domain}.{version}``
    """

    RIDES: str = "ridebooking.rides.v1"
    DRIVERS: str = "ridebooking.drivers.v1"
    NOTIFICATIONS: str = "ridebooking.notifications.v1"
    DLQ: str = "ridebooking.dlq.v1"


# ── Topic specifications ──────────────────────────────────────────────────

@dataclass
class TopicSpec:
    """Specification for a single Kafka topic."""

    name: str
    num_partitions: int
    replication_factor: int
    config: Dict[str, str]


def get_topic_specs(kafka_config: KafkaConfig | None = None) -> List[TopicSpec]:
    """Return the list of topics to create with their configurations.

    Args:
        kafka_config: Optional KafkaConfig; defaults to env-based config.

    Returns:
        A list of TopicSpec objects.
    """
    cfg = kafka_config or get_kafka_config()
    rf = cfg.default_replication_factor

    return [
        TopicSpec(
            name=Topics.RIDES,
            num_partitions=12,
            replication_factor=rf,
            config={
                "retention.ms": str(7 * 24 * 60 * 60 * 1000),   # 7 days
                "cleanup.policy": "delete",
                "min.insync.replicas": str(max(1, rf - 1)),
            },
        ),
        TopicSpec(
            name=Topics.DRIVERS,
            num_partitions=12,
            replication_factor=rf,
            config={
                "retention.ms": str(3 * 24 * 60 * 60 * 1000),   # 3 days
                "cleanup.policy": "delete",
                "min.insync.replicas": str(max(1, rf - 1)),
            },
        ),
        TopicSpec(
            name=Topics.NOTIFICATIONS,
            num_partitions=6,
            replication_factor=rf,
            config={
                "retention.ms": str(3 * 24 * 60 * 60 * 1000),   # 3 days
                "cleanup.policy": "delete",
                "min.insync.replicas": str(max(1, rf - 1)),
            },
        ),
        TopicSpec(
            name=Topics.DLQ,
            num_partitions=3,
            replication_factor=rf,
            config={
                "retention.ms": str(30 * 24 * 60 * 60 * 1000),  # 30 days
                "cleanup.policy": "delete",
                "min.insync.replicas": "1",
            },
        ),
    ]


def create_topics(kafka_config: KafkaConfig | None = None) -> None:
    """Create all required Kafka topics if they do not already exist.

    This is idempotent — existing topics are silently skipped.

    Args:
        kafka_config: Optional KafkaConfig; defaults to env-based config.
    """
    cfg = kafka_config or get_kafka_config()

    admin_conf = {"bootstrap.servers": cfg.bootstrap_servers}
    if cfg.security_protocol != "PLAINTEXT":
        admin_conf["security.protocol"] = cfg.security_protocol
    if cfg.sasl_mechanism:
        admin_conf["sasl.mechanism"] = cfg.sasl_mechanism
    if cfg.sasl_username:
        admin_conf["sasl.username"] = cfg.sasl_username
    if cfg.sasl_password:
        admin_conf["sasl.password"] = cfg.sasl_password

    admin = AdminClient(admin_conf)

    # Fetch existing topics
    try:
        existing_metadata = admin.list_topics(timeout=10)
        existing_topics = set(existing_metadata.topics.keys())
    except Exception as exc:
        logger.error("Failed to list Kafka topics: %s", exc)
        raise

    specs = get_topic_specs(cfg)
    new_topics: List[NewTopic] = []

    for spec in specs:
        if spec.name in existing_topics:
            logger.info("Topic '%s' already exists, skipping.", spec.name)
            continue
        new_topics.append(
            NewTopic(
                topic=spec.name,
                num_partitions=spec.num_partitions,
                replication_factor=spec.replication_factor,
                config=spec.config,
            )
        )

    if not new_topics:
        logger.info("All topics already exist. Nothing to create.")
        return

    logger.info(
        "Creating %d topic(s): %s",
        len(new_topics),
        [t.topic for t in new_topics],
    )

    futures = admin.create_topics(new_topics, operation_timeout=30)

    for topic_name, future in futures.items():
        try:
            future.result()  # block until complete
            logger.info("Created topic: %s", topic_name)
        except Exception as exc:
            # Topic already exists is not a fatal error
            if "TOPIC_ALREADY_EXISTS" in str(exc):
                logger.info("Topic '%s' already exists.", topic_name)
            else:
                logger.error("Failed to create topic '%s': %s", topic_name, exc)
                raise

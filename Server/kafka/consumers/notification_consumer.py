"""
Notification consumer.

Processes notification events from ``ridebooking.notifications.v1``
and delivers them to users/drivers via WebSocket.

Event types handled:
- ``notification.requested`` — deliver a notification via WebSocket

This consumer bridges the gap between Kafka (async, durable) and
WebSocket (real-time, ephemeral).  If a WebSocket connection is not
available, the notification is logged but not retried — the user
will see the update when they next poll or reconnect.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Set

from DataBase.Connection import SessionLocal
from DynamicDB.websockets.manager import manager
from kafka.consumer import BaseKafkaConsumer
from kafka.outbox.repository import OutboxRepository
from kafka.schemas import (
    EventEnvelope,
    EventType,
    NotificationRequestedPayload,
)
from kafka.topics import Topics

logger = logging.getLogger(__name__)


class NotificationConsumer(BaseKafkaConsumer):
    """Delivers notification events via WebSocket.

    Consumer group: ``ridebooking-notifications``
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            group_id="ridebooking-notifications",
            topics=[Topics.NOTIFICATIONS],
            **kwargs,
        )

    def get_handled_event_types(self) -> Optional[Set[str]]:
        return {
            EventType.NOTIFICATION_REQUESTED.value,
        }

    def handle_event(self, envelope: EventEnvelope) -> None:
        """Deliver a notification via WebSocket."""
        db = SessionLocal()
        try:
            # Idempotency check
            if OutboxRepository.is_event_processed(db, envelope.event_id):
                logger.debug(
                    "Duplicate notification skipped: %s", envelope.event_id,
                )
                self.metrics.record_duplicate()
                return

            payload: NotificationRequestedPayload = envelope.typed_payload()

            # Build the WebSocket message
            ws_message = {
                "type": payload.notification_type,
                "title": payload.title,
                "body": payload.body,
                **payload.data,
            }

            # Send via WebSocket (async → sync bridge)
            try:
                asyncio.run(
                    manager.send(
                        payload.recipient_role,
                        payload.recipient_id,
                        ws_message,
                    )
                )
                logger.info(
                    "Notification delivered: type=%s recipient=%s:%d",
                    payload.notification_type,
                    payload.recipient_role,
                    payload.recipient_id,
                )
            except Exception as exc:
                # WebSocket delivery failure is non-fatal
                logger.warning(
                    "WebSocket delivery failed for %s:%d: %s",
                    payload.recipient_role,
                    payload.recipient_id,
                    exc,
                )

            # Mark processed
            OutboxRepository.mark_event_processed(
                db,
                envelope.event_id,
                envelope.event_type,
                self._group_id,
            )
            db.commit()

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


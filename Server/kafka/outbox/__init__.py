"""
Transactional Outbox package.

Provides the Outbox pattern implementation:
- models.py  — OutboxEvent and ProcessedEvent SQLAlchemy models
- repository.py — Database operations for the outbox
- publisher.py — Background task that polls and publishes to Kafka
"""

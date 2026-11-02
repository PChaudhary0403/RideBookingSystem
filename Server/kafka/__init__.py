"""
Kafka event-driven pipeline package for the Ride Booking System.

This package provides:
- Centralized Kafka configuration (config.py)
- Event schema definitions with Pydantic validation (schemas.py)
- Topic management and initialization (topics.py)
- Producer with batching, compression, and idempotency (producer.py)
- Base consumer with error handling, retries, and DLQ (consumer.py)
"""

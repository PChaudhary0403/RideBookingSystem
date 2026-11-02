"""
Kafka consumer implementations for the Ride Booking System.

Consumers:
- ``RideLifecycleConsumer``  — processes ride events (matching, notifications)
- ``DriverLocationConsumer`` — processes driver location/availability events
- ``NotificationConsumer``   — delivers notifications via WebSocket
"""


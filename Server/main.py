import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Initialize structured logging before anything else
from logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

# Bug #4: Validate required environment variables at startup.
# Fail fast rather than letting the app start silently and break on first auth call.
_SECRET_KEY = os.getenv("SECRET_KEY")
_DATABASE_URL = os.getenv("DATABASE_URL")

if not _SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Set it in your .env file or deployment environment."
    )
if not _DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set it in your .env file or deployment environment."
    )

from routes.driver_routes import router as driver_router
from routes.vehicle_routes import router as vehicle_router
from routes.user_routes import router as user_router
from routes.ride_request_route import router as request_router
from routes.user_location import router as user_location_router  # Bug #7: register this router
from DynamicDB.websockets.driver_socket import router as driver_ws_router
from DynamicDB.websockets.user_socket import router as user_ws_router
from DataBase.Connection import Base, engine

# Create tables for any model that is imported here (development convenience only).
# Production deployments should use Alembic migrations instead.
from Trip.models.Trip import Trip                              # noqa: F401
from DynamicDB.models.triprequest import TripRequest           # noqa: F401
from UserSide.models.user_location import UserLocation         # noqa: F401
from UserSide.models.User import User                          # noqa: F401
from DriverSide.models.Driver import Rider                     # noqa: F401
from DriverSide.models.vehicle import Vehicle                  # noqa: F401
from DynamicDB.models.Driver_Location import DriverLocation    # noqa: F401
from DynamicDB.models.active_riders import ActiveDriver        # noqa: F401
from Trip.models.ride_request import RideRequest               # noqa: F401

# Kafka outbox models — imported so create_all() includes them
from kafka.outbox.models import OutboxEvent, ProcessedEvent     # noqa: F401


# ── Lifespan: startup / shutdown hooks ────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: start Kafka infrastructure, stop on shutdown."""
    # ── STARTUP ──
    logger.info("Application starting up...")

    # Create Kafka topics (idempotent)
    outbox_publisher = None
    try:
        from kafka.topics import create_topics
        create_topics()
        logger.info("Kafka topics verified/created.")
    except Exception as exc:
        logger.warning(
            "Kafka topic creation failed (Kafka may not be running): %s. "
            "The application will still start — topics can be created later.",
            exc,
        )

    # Start outbox publisher background task
    try:
        from kafka.outbox.publisher import OutboxPublisher
        outbox_publisher = OutboxPublisher()
        await outbox_publisher.start()
    except Exception as exc:
        logger.warning(
            "Outbox publisher failed to start: %s. "
            "Events will queue in the outbox table until Kafka is available.",
            exc,
        )

    # Start Kafka consumers in daemon threads
    try:
        from kafka.consumers.runner import start_consumers
        start_consumers()
    except Exception as exc:
        logger.warning(
            "Kafka consumers failed to start: %s. "
            "Run consumers separately with: python -m kafka.consumers.runner",
            exc,
        )

    yield  # ── APPLICATION RUNNING ──

    # ── SHUTDOWN ──
    logger.info("Application shutting down...")

    # Stop Kafka consumers
    try:
        from kafka.consumers.runner import stop_consumers
        stop_consumers()
    except Exception as exc:
        logger.error("Error stopping consumers: %s", exc)

    # Stop outbox publisher
    if outbox_publisher:
        try:
            await outbox_publisher.stop()
        except Exception as exc:
            logger.error("Error stopping outbox publisher: %s", exc)

    # Close Kafka producer
    try:
        from kafka.producer import close_producer
        close_producer()
    except Exception as exc:
        logger.error("Error closing Kafka producer: %s", exc)

    # Close Redis
    try:
        from kafka.redis_client import close_redis
        close_redis()
    except Exception as exc:
        logger.error("Error closing Redis: %s", exc)

    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Ride Booking System",
    description="Backend API for the Ride Booking System — Event-Driven Architecture",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://raahibooking.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/", tags=["health"])
def home():
    """Health check endpoint."""
    return {"message": "Backend Running", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    """Detailed health check."""
    return {"status": "ok", "service": "ride-booking-system"}


@app.get("/health/ready", tags=["health"])
def health_ready():
    """Readiness check: verifies DB, Kafka, and Redis connectivity."""
    checks = {}

    # Check PostgreSQL
    try:
        from DataBase.Connection import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["postgresql"] = "ok"
    except Exception as exc:
        checks["postgresql"] = f"error: {exc}"

    # Check Redis
    try:
        from kafka.redis_client import get_redis
        r = get_redis()
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    # Check Kafka producer
    try:
        from kafka.producer import get_producer
        producer = get_producer()
        checks["kafka_producer"] = "ok" if producer.is_healthy else "unhealthy"
    except Exception as exc:
        checks["kafka_producer"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


app.include_router(driver_router)
app.include_router(vehicle_router)
app.include_router(user_router)
app.include_router(request_router)
app.include_router(user_location_router)   # Bug #7: now registered
app.include_router(driver_ws_router)
app.include_router(user_ws_router)

# Prometheus metrics endpoint
from monitoring import metrics_router
app.include_router(metrics_router)

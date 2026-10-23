import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

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

app = FastAPI(
    title="Ride Booking System",
    description="Backend API for the Ride Booking System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ride-booking-system-sigma.vercel.app",
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


app.include_router(driver_router)
app.include_router(vehicle_router)
app.include_router(user_router)
app.include_router(request_router)
app.include_router(user_location_router)   # Bug #7: now registered
app.include_router(driver_ws_router)
app.include_router(user_ws_router)


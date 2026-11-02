"""
Ride request route — handles ride creation.

Updated to use ``RideLifecycleService`` for atomic ride creation
with transactional outbox event emission.  The Kafka consumer
handles driver matching asynchronously.

Preserves the existing API contract:
    POST /ride-request/ → {status: bool, trip_id: int, message: str}
"""

from DynamicDB.services.trip_request_Services import TripRequestServices
from DynamicDB.models.triprequest import TripRequest
from schemas.trip_request_schema import TripRequestResponse, TripRequestCreate
from DynamicDB.websockets.manager import manager
from auth.dependencies import get_current_user
from DataBase.Connection import get_db
from services.ride_service import RideLifecycleService
from services.rate_limiter import rate_limit_dependency
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ride-request",
    tags=["rideRequest"]
)
services = TripRequestServices()


@router.post(
    "/",
    response_model=TripRequestResponse,
    dependencies=[Depends(rate_limit_dependency("ride_request"))],
)
async def createRequest(
    data: TripRequestCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new ride request with transactional outbox event.

    The ride is persisted and a ``ride.requested`` event is atomically
    queued in the outbox.  The background outbox publisher sends the
    event to Kafka, and the ride lifecycle consumer triggers automatic
    driver matching.

    WebSocket notification to the driver is sent here for immediate
    feedback, while the Kafka pipeline handles durable processing.
    """
    # Atomic: create TripRequest + outbox event in one transaction
    result = RideLifecycleService.request_ride(
        db=db,
        user_id=user_id,
        driver_id=data.driver_id,
        pickup_lat=data.pickup_lat,
        pickup_long=data.pickup_long,
        dest_lat=data.dest_lat,
        dest_long=data.dest_long,
    )

    # Immediate WebSocket notification (best-effort, non-blocking)
    try:
        await manager.send(
            "driver",
            data.driver_id,
            {
                "type": "new request",
                "request": {
                    "user_id": user_id,
                    "driver_id": data.driver_id,
                    "pickup_lat": data.pickup_lat,
                    "pickup_long": data.pickup_long,
                    "dest_lat": data.dest_lat,
                    "dest_long": data.dest_long,
                }
            }
        )
    except Exception as exc:
        logger.warning(
            "WebSocket notification failed for driver %d: %s",
            data.driver_id,
            exc,
        )

    return {
        "status": True,
        "trip_id": result.id,
        "message": "Request received"
    }

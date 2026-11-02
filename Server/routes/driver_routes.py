"""
Driver routes — registration, auth, location, and ride management.

Updated to use ``RideLifecycleService`` for accept/reject with
transactional outbox events and race-condition protection.

All existing API contracts are preserved.
"""

from fastapi import APIRouter, Response, Cookie, HTTPException, Depends
from schemas.driver_schema import DriverCreate, DriverLogin
from DriverSide.services.rider_services import RiderService
from DynamicDB.services.trip_request_Services import TripRequestServices
from DynamicDB.services.active_rider_services import ActiveRiderServices
from schemas.DriveProfile import DriverProfileResponse
from schemas.DriverLocation import LocationGenerate
from DynamicDB.websockets.manager import manager
from schemas.trip_request_schema import (
    DriverTripRequest,
    DriverRequestResponse,
    TripRequestUpdate,
)
from auth.dependencies import get_current_driver
from DataBase.Connection import get_db
from services.ride_service import RideLifecycleService
from services.rate_limiter import rate_limit_dependency
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
router = APIRouter(
    prefix="/drivers",
    tags=["Register Driver"]
)
service = RiderService()


@router.post("/register")
def register_driver(driver: DriverCreate):
    rider = service.register_rider(
        driver.name,
        driver.surname,
        driver.email,
        driver.phone,
        driver.password,
        driver.address,
        driver.licenceno
    )
    return {
        "driverID": rider.id,
        "status": True,
        "message": "Driver Registered Successfully!"
    }


@router.post("/login", dependencies=[Depends(rate_limit_dependency("api_auth"))])
def login(driver: DriverLogin, response: Response):
    result = service.login(
        driver.email,
        driver.password,
    )
    if not result["success"]:
        if result["error"] == "USER_NOT_FOUND":
            return {"message": "No driver found"}
        if result["error"] == "INVALID_PASSWORD":
            return {"message": "Invalid password"}
    rider = result["rider"]
    token = jwt.encode(
        {
            "sub": str(rider.id),
            "role": "driver",
            "exp": datetime.utcnow() + timedelta(minutes=15),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    refresh_token = jwt.encode(
        {
            "sub": str(rider.id),
            "role": "driver",
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=30),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 15,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * 30,
    )
    return {
        "role": "driver",
        "status": True,
        "id": rider.id,        # Bug #13 fix: return driver id, matching user login
        "message": "login successful",
    }


@router.post("/logout")
def logout(
    response: Response,
    driver_id: int = Depends(get_current_driver),
):
    result = service.logout(driver_id)
    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["error"],
        )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {
        "status": True,
        "message": "Logged out successfully",
    }


@router.post("/refresh")
def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        driver_id = payload.get("sub")
        if driver_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = jwt.encode(
            {
                "sub": str(driver_id),
                "role": "driver",
                "exp": datetime.utcnow() + timedelta(minutes=15),
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=60 * 15,
        )
        return {"status": True, "message": "Access token refreshed"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/{driver_id}/profile", response_model=DriverProfileResponse)
def get_profile(driver_id: int):
    result = service.get_driver_profile(driver_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Driver Not found")
    rider = result["driver"]
    return {
        "status": True,
        "driver_id": rider.id,
        "name": rider.name,
        "surname": rider.surname,
        "rating": rider.rating,
        "total_reviews": rider.total_reviews,
    }


@router.post("/location", dependencies=[Depends(rate_limit_dependency("location_update"))])
def update_location(
    location: LocationGenerate,
    driver_id: int = Depends(get_current_driver),
):
    result = service.update_location(driver_id, location.latitude, location.longitude)
    if result is None:
        return {"message": "Driver not found"}
    return {
        "status": True,
        "driver_id": driver_id,
        "message": f"location updated successfully at {datetime.utcnow()}",
    }


trip_services = TripRequestServices()


@router.get("/get-request", response_model=DriverRequestResponse)
def get_request(driver_id: int = Depends(get_current_driver)):
    result = trip_services.get_request(driver_id)
    return {
        "status": True,
        "result": result,
        "message": "Request Retrieved Successfully",
    }


@router.patch(
    "/update-status/{trip_req_id}",
    dependencies=[Depends(rate_limit_dependency("driver_accept"))],
)
async def update_status(
    data: TripRequestUpdate,
    trip_req_id: int,
    driver_id: int = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """Accept or reject a ride request with transactional outbox events.

    Uses ``RideLifecycleService`` for atomic state changes with
    ``SELECT FOR UPDATE`` to prevent race conditions when multiple
    drivers attempt to accept the same ride.
    """
    try:
        if data.status == "accepted":
            update = RideLifecycleService.accept_ride(db, trip_req_id, driver_id)
        elif data.status == "rejected":
            update = RideLifecycleService.reject_ride(db, trip_req_id, driver_id)
        else:
            # Fallback: use existing service for non-lifecycle status updates
            update = trip_services.update_request(data.status, trip_req_id, driver_id)

        if not update:
            return {"status": False, "message": "Failed to update request status"}

        # Send WebSocket notification to user
        await manager.send(
            "user",
            update.user_id,
            {
                "type": "driver_response",
                "trip_req_id": update.id,
                "status": update.status,
            },
        )

        return {"status": True, "message": "Request Updated Successfully"}

    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Error updating ride status: trip=%d driver=%d error=%s",
            trip_req_id,
            driver_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/dismiss-request/{trip_req_id}")
def dismiss_request(
    trip_req_id: int,
    driver_id: int = Depends(get_current_driver),
):
    result = trip_services.dismiss_request(trip_req_id, driver_id)
    if not result:
        return {"status": False, "message": "Request not found"}
    return {"status": True, "message": "Request dismissed successfully"}


@router.get("/me")
def get_driverId(driver_id: int = Depends(get_current_driver)):
    return {"driver_id": driver_id}

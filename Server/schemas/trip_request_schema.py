from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class TripRequestResponse(BaseModel):
    """Response schema for a newly created trip request.

    Bug #5 fix: added 'status' field which the route always returned
    but the schema previously omitted.
    """
    status: bool
    trip_id: int
    message: str


class TripRequestCreate(BaseModel):
    driver_id: int
    pickup_lat: float
    pickup_long: float
    dest_lat: float
    dest_long: float


class DriverTripRequest(BaseModel):
    trip_req_id: int
    driver_id: int
    user_id: int
    pickup_lat: float
    pickup_long: float
    dest_lat: float
    dest_long: float
    status: str
    created_at: datetime


class DriverRequestResponse(BaseModel):
    status: bool
    result: list[DriverTripRequest]
    message: str


class TripStatus(str, Enum):
    """
    Valid trip request status values.

    Bug #14 fix: 'dismissed' (was 'dismiss') now matches the value
    written to the database in Trip_request_repo.dismiss_request().
    """
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    dismissed = "dismissed"   # was "dismiss" — now matches DB value
    cancelled = "cancelled"


class TripRequestUpdate(BaseModel):
    status: TripStatus

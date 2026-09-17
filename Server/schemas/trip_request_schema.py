from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class TripRequestResponse(BaseModel):
    trip_id: int
    message: str

class TripRequestCreate(BaseModel):
    driver_id:int
    pickup_lat:float
    pickup_long:float
    dest_lat:float
    dest_long:float

class DriverTripRequest(BaseModel):
    trip_req_id:int
    driver_id:int
    user_id:int
    pickup_lat: float
    pickup_long: float
    dest_lat: float
    dest_long: float
    status:str
    created_at:datetime

class DriverRequestResponse(BaseModel):
    status:bool
    result:list[DriverTripRequest]
    message:str

class TripStatus(str,Enum):
    pending="pending"
    accepted="accepted"
    rejected="rejected"
    completed="completed"
    dismiss="dismiss"

class TripRequestUpdate(BaseModel):
    status:TripStatus

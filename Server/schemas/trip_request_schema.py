from pydantic import BaseModel
from datetime import datetime

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
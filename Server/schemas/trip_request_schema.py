from pydantic import BaseModel
from datetime import datetime

class TripRequestResponse(BaseModel):
    trip_id: int
    message: str

class TripRequestCreate(BaseModel):
    driver_id:int

class DriverTripRequest(BaseModel):
    driver_id:int
    user_id:int
    status:str
    created_at:datetime

class DriverRequestResponse(BaseModel):
    status:bool
    result:list[DriverTripRequest]
    message:str
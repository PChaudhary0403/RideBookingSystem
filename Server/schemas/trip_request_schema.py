from pydantic import BaseModel

class TripRequestResponse(BaseModel):
    trip_id: int
    message: str

class TripRequestCreate(BaseModel):
    driver_id:int
from pydantic import BaseModel
from datetime import datetime
class CreateTrip(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dest_lat: float
    dest_lng: float
from pydantic import BaseModel
class NearbyDriversRequest(BaseModel):
    latitude:float
    longitude:float
    radius_km:float=30
    
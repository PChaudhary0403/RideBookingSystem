from pydantic import BaseModel
class DriverProfileResponse(BaseModel):
    driver_id:int
    name:str
    surname:str
    rating:float|None=None
    total_reviews:int=0
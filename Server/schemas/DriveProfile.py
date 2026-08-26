from pydantic import BaseModel
class DriverProfileResponse(BaseModel):
    id:int
    name:str
    surname:str
    rating:float|None=None
    total_reviews:int=0
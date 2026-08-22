from pydantic import BaseModel
class LocationGenerate(BaseModel):
    latitude:float
    longitude:float
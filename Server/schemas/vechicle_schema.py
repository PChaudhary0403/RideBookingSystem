from pydantic import BaseModel
from DriverSide.models.vehicle import VehicleType
class VehicleCreate(BaseModel):
    name:str
    vehicle_type:VehicleType
    registration_number:str
    associated_licence:str
    city:str
    state:str
    mileage:int
    parent_company:str
    model:str
    color:str
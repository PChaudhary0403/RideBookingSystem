from fastapi import APIRouter
from schemas.vechicle_schema import VehicleCreate
from DriverSide.services.vehicle_services import VehicleService
from fastapi import APIRouter,Depends,HTTPException
from auth.dependencies import get_current_driver
router=APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)
service=VehicleService()
@router.post("/")
def register_vehicle(vehicle:VehicleCreate,driver_id:int=Depends(get_current_driver)):
    result=service.register_vehicle(
        driver_id,
        vehicle.name,
        vehicle.vehicle_type,
        vehicle.registration_number,
        vehicle.associated_licence,
        vehicle.city,
        vehicle.state,
        vehicle.mileage,
        vehicle.parent_company,
        vehicle.model,
        vehicle.color
    )
    return{
        "vehicle_id":result.id,
        "driver_id":result.driver_id,
        "message":"Vehicle registered successfully!"
    }

@router.get("/driver/{driver_id}")

def get_driver_vehicles(driver_id:int):
    vehicles=service.get_driver_vehicles(driver_id)
    return{
        "driver_id":driver_id,
        "vehicles":vehicles
    }


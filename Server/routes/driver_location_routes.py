from fastapi import APIRouter,Depends
from schemas.driver_location import LocationGenerate
from DynamicDB.services.driver_location_services import DriverLocationService
from auth.dependencies import get_current_driver
router=APIRouter(
    prefix='/drivers',
    tags=["locationUpdate"]
)
service=DriverLocationService()
@router.post("/location")
def update_location(
    location:LocationGenerate,
    driver_id:int =Depends(get_current_driver)):
    result=service.update_location(driver_id,location.latitude,location.longitude)
    return{
        "status":True,
        "driver_id":driver_id,
        "latitude":result.latitude,
        "longitude":result.longitude,
        "message":"location updated successfully"
}

from fastapi import APIRouter,Depends
from Server.schemas.user_location import LocationGenerate
from UserSide.services.user_location_services import UserLocationService
from auth.dependencies import get_current_driver
router=APIRouter(
    prefix='/users',
    tags=["locationUpdate"]
)
service=UserLocationService()
@router.post("/location")
def update_location(
    location:LocationGenerate,
    user_id:int =Depends(get_current_driver)):
    result=service.update_location(user_id,location.latitude,location.longitude)
    return{
        "status":True,
        "driver_id":user_id,
        "latitude":result.latitude,
        "longitude":result.longitude,
        "message":"location updated successfully"
}

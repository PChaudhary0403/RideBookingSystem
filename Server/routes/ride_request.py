from DynamicDB.services.trip_request_Services import TripRequestServices
from DynamicDB.models.triprequest import TripRequest
from schemas.trip_request_schema import TripRequestResponse,TripRequestCreate
from auth.dependencies import  get_current_user
from fastapi import APIRouter,Depends
router=APIRouter(
    prefix="/ride-request",
    tags=["rideRequest"]
)
services=TripRequestServices()
@router.post("/",response_model=TripRequestResponse)
def createRequest(data:TripRequestCreate,user_id:int=Depends(get_current_user)
):
    result=services.registerRequest(data.driver_id,user_id)
    return {
        "status":True,
        "trip_id":result.id,
        "message":"Request recieved"
    }


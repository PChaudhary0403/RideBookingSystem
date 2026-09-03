from DynamicDB.services.trip_request_Services import TripRequestServices
from DynamicDB.models.triprequest import TripRequest
from schemas.trip_request_schema import TripRequestResponse,TripRequestCreate
from DynamicDB.websockets.manager import manager
from auth.dependencies import  get_current_user
from fastapi import APIRouter,Depends
router=APIRouter(
    prefix="/ride-request",
    tags=["rideRequest"]
)
services=TripRequestServices()
@router.post("/",response_model=TripRequestResponse)
async def createRequest(data:TripRequestCreate,user_id:int=Depends(get_current_user)
):
    print(data.driver_id)
    result=services.registerRequest(
        data.driver_id,
        user_id,
        data.pickup_lat,
        data.pickup_long,
        data.dest_lat,
        data.dest_long)
    await manager.send_to_driver(
        data.driver_id,
        {
            "type":"new request",
            "request":{
                "trip_id":result.id,
                "user_id":user_id,
                "driver_id":data.driver_id,
                "pickup_lat":data.pickup_lat,
                "pickup_long":data.pickup_long,
                "dest_lat":data.dest_lat,
                "dest_long":data.dest_long
            }
        }
    )
    return {
        "status":True,
        "trip_id":result.id,
        "message":"Request recieved"
    }


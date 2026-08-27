from fastapi import APIRouter
from schemas.trip_schema import CreateTrip
from Trip.models.Trip import Trip
from Trip.repositories.trip_repo import TripRepository
from Trip.services.trip_services import TripServices
router=APIRouter(
    prefix="/trip",
    tags=["trip_data"]
)
services=TripServices()
# @router.post("/get_request")
# def get_request(trip:)

@router.post("/get_trip")
def get_trip(trip:CreateTrip):
    trip_=services.register_trip(
        trip.pickup_lat,
        trip.pickup_lng,
        trip.dest_lat,
        trip.dest_lng
    )
    return{
        "id":trip_.trip_id,
        "message":"Trip connected"
    }


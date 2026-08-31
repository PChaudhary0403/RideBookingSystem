from Trip.models.ride_request import RideRequest
from Trip.repositories.ride_request_repo import RequestRepository
class RequestServices:
    def register_request(
            self,
            user_id,
            driver_id,
            pickup_latitude,
            pickup_longitude,
            destination_latitude,
            destination_longitude
    ):
        trip=RideRequest(
            user_id=user_id,
            driver_id=driver_id,
            pickup_latitude=pickup_latitude,
            pickup_longitude=pickup_longitude,
            destination_latitude=destination_latitude,
            destination_longitude=destination_longitude
            )
        RequestRepository.add(trip)
        return trip
        
from Trip.models.ride_request import RideRequest
from Trip.repositories.ride_request_repo import RequestRepository
class RequestServices:
    def register_request(
            self,
            user_id,
            driver_id
    ):
        trip=RideRequest(
            user_id=user_id,
            driver_id=driver_id
            )
        RequestRepository.add(trip)
        return trip
        
from DynamicDB.models.triprequest import TripRequest
from DynamicDB.repositories.Trip_request_repo import TripRequestRepository
class TripRequestServices:
    def registerRequest(self,driver_id,user_id,pickup_lat,pickup_long,dest_lat,dest_long):
        request=TripRequest(
            driver_id=driver_id,
            user_id=user_id,
            pickup_lat=pickup_lat,
            pickup_long=pickup_long,
            dest_lat=dest_lat,
            dest_long=dest_long
        )
        TripRequestRepository.add(request)
        return request

    def get_request(self,driver_id):
        return TripRequestRepository.get_requests(driver_id=driver_id)
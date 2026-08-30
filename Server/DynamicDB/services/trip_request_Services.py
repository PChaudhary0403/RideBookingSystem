from DynamicDB.models.triprequest import TripRequest
from DynamicDB.repositories.Trip_request_repo import TripRequestRepository
class TripRequestServices:
    def registerRequest(self,driver_id,user_id):
        request=TripRequest(
            driver_id=driver_id,
            user_id=user_id
        )
        TripRequestRepository.add(request)
        return request
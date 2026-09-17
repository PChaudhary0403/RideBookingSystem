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

    def dismiss_request(self,trip_req_id,driver_id):
        return TripRequestRepository.dismiss_request(trip_req_id=trip_req_id,driver_id=driver_id)

    def update_request(self,status,trip_req_id,driver_id):
        return TripRequestRepository.update_request(status=status,trip_req_id=trip_req_id,driver_id=driver_id)

    def get_driver_response(self,trip_req_id,user_id):
        return TripRequestRepository.get_driver_response(trip_req_id=trip_req_id,user_id=user_id)
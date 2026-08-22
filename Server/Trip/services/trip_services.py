from Trip.models.Trip import Trip
from Trip.repositories.trip_repo import TripRepository

class TripServices:
    def register_trip(self,
            trip_id,
            requested_at,
            accepted_at,
            driver_arrived_at,
            started_at,
            pickup_lat,
            pickup_lng,
            completed_at,
            dest_lat,
            dest_lng,
            status
    ):
        trip=Trip(
            trip_id=trip_id,
            requested_at=requested_at,
            accepted_at=accepted_at,
            driver_arrived_at=driver_arrived_at,
            started_at=started_at,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            completed_at=completed_at,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            status=status
        )
        TripRepository.add(trip)
        return trip
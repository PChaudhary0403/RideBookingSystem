from DynamicDB.repositories.driver_location_repo import Driver_Location_Repository
class DriverLocationService:
    def update_location(self,driver_id,latitude,longitude):
        return Driver_Location_Repository(
            driver_id,
            latitude,
            longitude
        )
from DataBase.Connection import SessionLocal
from DynamicDB.models.Driver_Location import DriverLocation

class Driver_Location_Repository:
    @staticmethod
    def update_location(driver_id,latitude,longitude):
        db=SessionLocal()
        try:
            location=db.query(DriverLocation).filter(
                DriverLocation.driver_id==driver_id
            ).first()
            if location is None:
                location==DriverLocation(
                    driver_id=driver_id,
                    latitude=latitude,
                    longitude=longitude
                )
                db.add(location)
            else:
                location.latitude=latitude
                location.longitude=longitude
            db.commit()
            db.refresh(location)
            return location
        finally:
            db.close()
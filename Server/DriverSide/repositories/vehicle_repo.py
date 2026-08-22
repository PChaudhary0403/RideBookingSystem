from DataBase.Connection import SessionLocal
from DriverSide.models.vehicle import Vehicle
class VehicleRepository:
    @staticmethod
    def add(vehicle):
        db=SessionLocal()
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        db.close()

    def show_vehicle(driver_id):
        db=SessionLocal()
        try:
            return db.query(Vehicle).filter(Vehicle.driver_id==driver_id).all()
        finally:
            db.close()
        
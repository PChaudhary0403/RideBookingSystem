from Trip.models.ride_request import RideRequest
from DataBase.Connection import SessionLocal
class RequestRepository:
    @staticmethod
    def add(trip):
        db=SessionLocal()
        db.add(trip)
        db.commit()
        db.refresh(trip)
        db.close()
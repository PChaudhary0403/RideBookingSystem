from DataBase.Connection import SessionLocal
from Trip.models import Trip
class TripRepository:
    @staticmethod
    def add(trip):
        db=SessionLocal()
        db.add(trip)
        db.commit()
        db.refresh(trip)
        db.close()
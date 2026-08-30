from DataBase.Connection import SessionLocal
from DynamicDB.models.triprequest import TripRequest
class TripRequestRepository:
    @staticmethod
    def add(Request):
        db=SessionLocal()
        db.add(Request)
        db.commit()
        db.refresh(Request)
        db.close()


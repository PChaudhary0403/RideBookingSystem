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

    @staticmethod
    def get_requests(driver_id):
        db=SessionLocal()
        try:
            return db.query(TripRequest).filter(
                TripRequest.driver_id==driver_id,
                TripRequest.status=="pending"
            ).order_by(TripRequest.created_at.desc()).all()
        finally:
            db.close()

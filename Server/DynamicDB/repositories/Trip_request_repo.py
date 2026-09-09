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
    def get_requests(driver_id:int):
        db=SessionLocal()
        try:
            requests=(
                db.query(TripRequest).filter(
                TripRequest.driver_id==driver_id,
                TripRequest.status=="pending"
            ).order_by(TripRequest.created_at.desc()).all()
            )
            return [
        {
            "trip_id": request.id,
            "driver_id": request.driver_id,
            "user_id": request.user_id,
            "pickup_lat": request.pickup_lat,
            "pickup_long": request.pickup_long,
            "dest_lat": request.dest_lat,
            "dest_long": request.dest_long,
            "status": request.status,
            "created_at": request.created_at
        }
        for request in requests
    ]
        finally:
            db.close()

    def dismiss_request(trip_id: int, driver_id: int):

        db = SessionLocal()
        try:
            request = (
                db.query(TripRequest)
                .filter(
                    TripRequest.id == trip_id,
                    TripRequest.driver_id == driver_id,
                    TripRequest.status == "pending"
                )
                .first()
            )
            if not request:
                return None
            request.status = "dismissed"
            db.commit()
            return request
        finally:
            db.close()

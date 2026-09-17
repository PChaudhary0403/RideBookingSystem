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
            "trip_req_id": request.id,
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

    @staticmethod
    def dismiss_request(trip_req_id: int, driver_id: int):

        db = SessionLocal()
        try:
            request = (
                db.query(TripRequest)
                .filter(
                    TripRequest.id == trip_req_id,
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

    @staticmethod
    def update_request(status,trip_req_id:int,driver_id:int):
        db=SessionLocal()
        try:
            request=(
                db.query(TripRequest).filter(
                    TripRequest.id==trip_req_id,
                    TripRequest.driver_id==driver_id,
                ).first()
            )
            if request is None:
                print("No request Found")
                return None
            request.status=status
            db.commit()
            db.refresh(request)
            print("Updated request status",request)
            return request
        finally:
            db.close()

    def get_driver_response(trip_req_id:int,user_id:int):
        db=SessionLocal()
        try:
            request=(
                db.query(TripRequest).filter(
                    TripRequest.id==trip_req_id,
                    TripRequest.user_id==user_id,
                ).first()
            )
            if request is None:
                return None
            return{
                "status":request.status
            }
        finally:
            db.close()

    def call_driver(trip_req_id:int,user_id:int):
        db=SessionLocal()
        try:
            request=(
                db.query(TripRequest).filter(
                    TripRequest.id==trip_req_id,
                    TripRequest.user_id==user_id,
                    TripRequest.status=="accepted"
                ).first()
            )
            return request
        finally:
            db.close()
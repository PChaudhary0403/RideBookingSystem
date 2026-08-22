from DataBase.Connection import SessionLocal
from UserSide.models.user_location import UserLocation

class User_Location_Repository:
    @staticmethod
    def update_location(user_id,latitude,longitude):
        db=SessionLocal()
        try:
            location=db.query(UserLocation).filter(
                UserLocation.user_id==user_id
            ).first()
            if location is None:
                location==UserLocation(
                    user_id=user_id,
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
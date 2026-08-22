from UserSide.models.User import User
from UserSide.repositories.user_repo import UserRepository
from DynamicDB.repositories.active_rider_repo import ActiveDriverRepository
from utils.distance import calculate_distance
from datetime import datetime,timezone

class UserService:
    def register_user(self,name,phone,emailID,password):
        user=User(name=name,
                   phone=phone,
                    emailID=emailID,
                    password=password
                    )
        UserRepository.add(user)
        return user

    def login(self,emailID,password):
        user=UserRepository.find_by_email(emailID=emailID)
        if user is None:
            return {"success":False,"error":"USER_NOT_FOUND"}
        if user.password != password:
            return {"success":False,"error":"INVALID_PASSWORD"}
        return {
            "success":True,
            "user":user
        }


    def get_nearby_drivers(self,user_lat,user_lng,radius_km=5):
        drivers=ActiveDriverRepository.get_active_drivers_with_location()
        nearby_drivers=[]
        for active_driver,location in drivers:
            distance=calculate_distance(
                user_lat,
                user_lng,
                location.latitude,
                location.langitude
            )
            if distance<=radius_km:
                nearby_drivers.append({
                    "driver_id":active_driver.id,
                    "latitude":location.latitude,
                    "longitude":location.longitude,
                    "distance_km":round(distance,2)
                    })
        return nearby_drivers

    def logout(self, user_id):
        user = UserRepository.update_status(
            user_id=user_id,
            is_online=False,
            is_available=False,
            last_seen=datetime.now(timezone.utc)
        )

        if user is None:
            return {
                "success": False,
                "error": "DRIVER_NOT_FOUND"
            }
        print("is_online: ",user.is_online)
        return {
            "success": True
        }
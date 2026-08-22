from UserSide.repositories.user_location_repo import User_Location_Repository
class UserLocationService:
    def update_location(self,user_id,latitude,longitude):
        return User_Location_Repository(
            user_id,
            latitude,
            longitude
        )
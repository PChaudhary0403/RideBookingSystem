from DriverSide.models.Driver import Rider
from DriverSide.repositories.rider_repo import RiderRepository
from DynamicDB.repositories.active_rider_repo import ActiveDriverRepository
from datetime import datetime,timezone

class RiderService:
    def register_rider(self,name,surname,email,phone,password,address,licenseno):
        rider=Rider(name=name,
                    surname=surname,
                    email=email,
                    phone=phone,
                    password=password,
                    address=address,
                    licenceno=licenseno,
                    permit=True,
                    )
        RiderRepository.add(rider)
        return rider

    def login(self,email,password):
        rider=RiderRepository.find_by_email(email=email)
        if rider is None:
            return {"success":False,"error":"USER_NOT_FOUND"}

        if rider.password != password:
            return {"success":False,"error":"INVALID_PASSWORD"}
        ActiveDriverRepository.upsert(
        driver_id=rider.id,
        is_online=True,
        is_available=True
        )
        return {
            "success":True,
            "rider":rider
        }

    def logout(self, driver_id):
        rider = ActiveDriverRepository.update_status(
            driver_id=driver_id,
            is_online=False,
            is_available=False,
            last_seen=datetime.now(timezone.utc)
        )

        if rider is None:
            return {
                "success": False,
                "error": "DRIVER_NOT_FOUND"
            }
        print("is_online: ",rider.is_online)
        return {
            "success": True
        }
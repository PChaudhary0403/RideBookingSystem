from DataBase.Connection import SessionLocal
from DynamicDB.models.active_riders import ActiveDriver
from DynamicDB.models.Driver_Location import DriverLocation
from datetime import datetime,timezone
class ActiveDriverRepository:
    @staticmethod
    def add(ActiveDriver):
        db=SessionLocal()
        db.add(ActiveDriver)
        db.commit()
        db.refresh(ActiveDriver)
        db.close()

    @staticmethod
    def find_by_id(driver_id):
        db=SessionLocal()
        try:
            return db.query(ActiveDriver).filter(ActiveDriver.driver_id==driver_id).first()
        finally:
            db.close()

    def update_status(driver_id,is_online,is_available,last_seen=None):
        db=SessionLocal()
        try:
            rider=db.query(ActiveDriver).filter(ActiveDriver.driver_id==driver_id).first()
            if rider is None:
                return None
            rider.is_online=is_online
            rider.is_available=is_available
            if last_seen is not None:
                rider.last_seen=last_seen
            db.commit()
            db.refresh(rider)
            return rider
        finally:
            db.close()

    def logout(self, driver_id):

        driver = ActiveDriverRepository.update_status(
            driver_id=driver_id,
            is_online=False,
            is_available=False,
            last_seen=datetime.now(timezone.utc)
        )

        if driver is None:
            return {
                "success": False,
                "error": "DRIVER_NOT_FOUND"
            }

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    @staticmethod
    def upsert(driver_id, is_online, is_available):
        db = SessionLocal()

        try:
            active_driver = (
                db.query(ActiveDriver)
                .filter(ActiveDriver.driver_id == driver_id)
                .first()
            )

            if active_driver:
                active_driver.is_online = is_online
                active_driver.is_available = is_available
                active_driver.last_seen = datetime.now(timezone.utc)

            else:
                active_driver = ActiveDriver(
                    driver_id=driver_id,
                    is_online=is_online,
                    is_available=is_available,
                    last_seen=datetime.now(timezone.utc)
                )

                db.add(active_driver)

            db.commit()
            db.refresh(active_driver)

            return active_driver

        finally:
            db.close()

    def get_active_drivers_with_location():
        db=SessionLocal()
        try:
            drivers=(
                db.query(ActiveDriver,DriverLocation)
                .join(DriverLocation,ActiveDriver.driver_id==DriverLocation.driver_id)
                .filter(ActiveDriver.is_online==True,ActiveDriver.is_available==True).all()
            )
            return drivers
        finally:
            db.close()
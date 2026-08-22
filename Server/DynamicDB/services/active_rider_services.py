from DynamicDB.models.active_riders import  ActiveDriver
from DynamicDB.repositories.active_rider_repo import ActiveDriverRepository
from datetime import datetime,timezone

class ActiveRiderServices:
    def set_online(self,driver_id):
        rider=ActiveDriverRepository.update_online_status(driver_id=driver_id,is_online=True,last_seen=datetime.now(timezone.utc))
        if rider is None:
            return False
        return True

    def set_offline(self,driver_id):
        rider=ActiveDriverRepository.update_online_status(driver_id=driver_id,is_online=False,last_seen=datetime.now(timezone.utc))
        if rider is None:
            return False
        return True
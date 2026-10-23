from DynamicDB.models.active_riders import ActiveDriver
from DynamicDB.repositories.active_rider_repo import ActiveDriverRepository
from datetime import datetime, timezone


class ActiveRiderServices:
    def set_online(self, driver_id):
        """Mark a driver as online. Bug #6 fix: calls update_status() not update_online_status()."""
        rider = ActiveDriverRepository.update_status(
            driver_id=driver_id,
            is_online=True,
            is_available=True,
            last_seen=datetime.now(timezone.utc)
        )
        if rider is None:
            return False
        return True

    def set_offline(self, driver_id):
        """Mark a driver as offline. Bug #6 fix: calls update_status() not update_online_status()."""
        rider = ActiveDriverRepository.update_status(
            driver_id=driver_id,
            is_online=False,
            is_available=False,
            last_seen=datetime.now(timezone.utc)
        )
        if rider is None:
            return False
        return True
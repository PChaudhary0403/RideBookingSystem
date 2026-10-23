from fastapi import APIRouter, Depends
from schemas.user_location import UserLocationUpdate   # Bug #7: fixed import path (no 'Server.' prefix)
from UserSide.services.user_location_services import UserLocationService
from auth.dependencies import get_current_user          # Bug #7: fixed to use user guard, not driver guard

router = APIRouter(
    prefix="/users",
    tags=["user-location"]
)
service = UserLocationService()


@router.post("/location")
def update_user_location(
    location: UserLocationUpdate,
    user_id: int = Depends(get_current_user)   # Bug #7: correct guard
):
    """Update the authenticated user's current location."""
    result = service.update_location(user_id, location.latitude, location.longitude)
    return {
        "status": True,
        "user_id": user_id,
        "latitude": result.latitude,
        "longitude": result.longitude,
        "message": "Location updated successfully"
    }


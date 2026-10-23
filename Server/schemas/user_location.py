from pydantic import BaseModel, Field


class UserLocationUpdate(BaseModel):
    """User location update payload with coordinate validation."""
    latitude: float = Field(
        ..., ge=-90.0, le=90.0, description="Latitude (-90 to 90)"
    )
    longitude: float = Field(
        ..., ge=-180.0, le=180.0, description="Longitude (-180 to 180)"
    )
from pydantic import BaseModel, Field


class LocationGenerate(BaseModel):
    """Driver location update payload with coordinate validation."""
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90 to 90)"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180 to 180)"
    )

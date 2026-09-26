from pydantic import BaseModel, Field


class PoiCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    address: str = Field(min_length=1)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    trigger_radius_meters: float = Field(
        default=2,
        ge=1,
        le=2,
    )


class PoiVisibility(BaseModel):
    is_active: bool


class PoiResponse(PoiCreate):
    id: int
    is_active: bool


class NearbyPoiResponse(PoiResponse):
    distance_meters: float

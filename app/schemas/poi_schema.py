from pydantic import BaseModel, Field


class PoiCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    address: str = Field(min_length=1)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    trigger_radius_meters: int = Field(
        default=30,
        gt=0,
        le=500
    )


class PoiVisibility(BaseModel):
    is_active: bool


class PoiResponse(PoiCreate):
    id: int
    is_active: bool

class NearbyPoiResponse(PoiResponse):
    distance_meters: float
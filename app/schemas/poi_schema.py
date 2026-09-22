from pydantic import BaseModel, Field


class PoiCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    address: str = Field(min_length=1)


class PoiVisibility(BaseModel):
    is_active: bool


class PoiResponse(PoiCreate):
    id: int
    is_active: bool
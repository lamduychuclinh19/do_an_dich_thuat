from typing import Literal

from fastapi import APIRouter, Query

from app.schemas.guide_schema import NearbyGuideResponse
from app.services.guide_service import guide_service


router = APIRouter(
    prefix="/api/public/guide",
    tags=["PUBLIC - Visitor Guide"],
)


@router.get(
    "/nearby",
    response_model=NearbyGuideResponse | None,
)
def get_nearby_guide(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    language_code: Literal[
        "Viet Nam",
        "English",
        "France",
        "Chinese",
        "Korean",
    ] = Query(...),
):
    return guide_service.get_nearby_guide(
        latitude=latitude,
        longitude=longitude,
        language_code=language_code,
    )
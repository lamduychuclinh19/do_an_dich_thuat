from fastapi import APIRouter

from app.schemas.poi_schema import PoiResponse
from app.services.poi_service import poi_service


router = APIRouter(
    prefix="/api/public/pois",
    tags=["PUBLIC - POIs"],
)


@router.get(
    "",
    response_model=list[PoiResponse],
)
def get_all_pois():
    return poi_service.get_all_pois()


@router.get(
    "/{poi_id}",
    response_model=PoiResponse,
)
def get_poi_by_id(poi_id: int):
    return poi_service.get_poi_by_id(poi_id)
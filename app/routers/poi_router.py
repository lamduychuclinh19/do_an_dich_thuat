from fastapi import APIRouter, status

from app.schemas.poi_schema import PoiCreate, PoiResponse
from app.services.poi_service import poi_service


router = APIRouter(
    prefix="/api/pois",
    tags=["POIs"]
)


@router.post(
    "",
    response_model=PoiResponse,
    status_code=status.HTTP_201_CREATED
)
def create_poi(data: PoiCreate):
    return poi_service.create_poi(data)


@router.get("", response_model=list[PoiResponse])
def get_all_pois():
    return poi_service.get_all_pois()
"""API công khai đọc các địa điểm đang được hiển thị."""

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
    """Trả các địa điểm đang công khai cho khách tham quan."""
    return poi_service.get_all_pois()


@router.get(
    "/{poi_id}",
    response_model=PoiResponse,
)
def get_poi_by_id(poi_id: str):
    """Tìm một địa điểm công khai theo mã POI."""
    return poi_service.get_poi_by_id(poi_id)

from fastapi import APIRouter, status

from app.schemas.poi_schema import PoiCreate, PoiResponse, PoiVisibility
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


@router.get("/{poi_id}", response_model=PoiResponse)
def get_poi_by_id(poi_id: int):
    return poi_service.get_poi_by_id(poi_id)

@router.put("/{poi_id}", response_model=PoiResponse)
def update_poi(poi_id: int, data: PoiCreate):
    return poi_service.update_poi(poi_id, data)

@router.patch(
    "/{poi_id}/visibility",
    response_model=PoiResponse
)
def set_poi_visibility(
    poi_id: int,
    data: PoiVisibility
):
    return poi_service.set_poi_visibility(poi_id, data)
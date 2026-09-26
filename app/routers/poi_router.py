from fastapi import APIRouter, Query, status

from app.schemas.poi_schema import NearbyPoiResponse, PoiCreate, PoiResponse, PoiVisibility
from app.services.poi_service import poi_service
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth_dependency import require_admin


router = APIRouter(
    prefix="/api/pois",
    tags=["POIs"]
)


@router.post(
    "",
    response_model=PoiResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_poi(data: PoiCreate):
    return poi_service.create_poi(data)


@router.get("", response_model=list[PoiResponse])
def get_all_pois():
    return poi_service.get_all_pois()

@router.get("/nearby",response_model=NearbyPoiResponse | None)
def find_nearby_poi(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180)
):
    return poi_service.find_nearby_poi(
        latitude,
        longitude
    )

@router.get("/{poi_id}", response_model=PoiResponse)
def get_poi_by_id(poi_id: int):
    return poi_service.get_poi_by_id(poi_id)

@router.put(
    "/{poi_id}",
    response_model= PoiResponse,
    dependencies=[Depends(require_admin)],
)
@router.patch(
    "/{poi_id}/visibility",
    response_model= PoiResponse,
    dependencies=[Depends(require_admin)],
)
def set_poi_visibility(
    poi_id: int,
    data: PoiVisibility
):
    return poi_service.set_poi_visibility(poi_id, data)
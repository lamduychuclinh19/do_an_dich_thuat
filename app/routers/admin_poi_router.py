from fastapi import APIRouter, Depends, status

from app.dependencies.auth_dependency import require_admin
from app.schemas.poi_schema import (
    PoiCreate,
    PoiResponse,
    PoiVisibility,
)
from app.services.poi_service import poi_service


router = APIRouter(
    prefix="/api/admin/pois",
    tags=["ADMIN - POIs"],
    dependencies=[Depends(require_admin)],
)

@router.get(
    "",
    response_model=list[PoiResponse],
)
def get_all_pois_for_admin():
    return poi_service.get_all_pois_for_admin()


@router.post(
    "",
    response_model=PoiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_poi(data: PoiCreate):
    return poi_service.create_poi(data)


@router.put(
    "/{poi_id}",
    response_model=PoiResponse,
)
def update_poi(
    poi_id: int,
    data: PoiCreate,
):
    return poi_service.update_poi(
        poi_id,
        data,
    )


@router.patch(
    "/{poi_id}/visibility",
    response_model=PoiResponse,
)
def set_poi_visibility(
    poi_id: int,
    data: PoiVisibility,
):
    return poi_service.set_poi_visibility(
        poi_id,
        data,
    )
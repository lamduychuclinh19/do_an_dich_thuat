"""API quản lý POI dùng chung cho SYSTEM_ADMIN và SHOP_OWNER."""

from fastapi import APIRouter, Depends, status

from app.dependencies.auth_dependency import require_back_office
from app.schemas.poi_schema import (
    BackOfficePoiCreate,
    BackOfficePoiResponse,
    PoiCreate,
    PoiVisibility,
)
from app.services.poi_service import poi_service


router = APIRouter(
    prefix="/api/admin/pois",
    tags=["BACK OFFICE - POIs"],
)


@router.get(
    "",
    response_model=list[BackOfficePoiResponse],
)
def get_all_pois_for_back_office(
    current_person: dict = Depends(require_back_office),
):
    """SYSTEM_ADMIN xem tất cả; SHOP_OWNER chỉ xem POI của mình."""
    return poi_service.get_all_pois_for_back_office(current_person)


@router.post(
    "",
    response_model=BackOfficePoiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_poi(
    data: BackOfficePoiCreate,
    current_person: dict = Depends(require_back_office),
):
    """Tạo POI và xác định chủ sở hữu theo vai trò đang đăng nhập."""
    poi_data = PoiCreate(
        **data.model_dump(exclude={"id", "owner_id"})
    )

    return poi_service.create_poi_for_back_office(
        data=poi_data,
        current_person=current_person,
        requested_poi_id=data.id,
        requested_owner_id=data.owner_id,
    )


@router.put(
    "/{poi_id}",
    response_model=BackOfficePoiResponse,
)
def update_poi(
    poi_id: str,
    data: PoiCreate,
    current_person: dict = Depends(require_back_office),
):
    """Cập nhật POI theo phạm vi quyền của tài khoản hiện tại."""
    return poi_service.update_poi_for_back_office(
        poi_id=poi_id,
        data=data,
        current_person=current_person,
    )


@router.patch(
    "/{poi_id}/visibility",
    response_model=BackOfficePoiResponse,
)
def set_poi_visibility(
    poi_id: str,
    data: PoiVisibility,
    current_person: dict = Depends(require_back_office),
):
    """Ẩn/hiện POI theo phạm vi quyền, không xóa dữ liệu."""
    return poi_service.set_poi_visibility_for_back_office(
        poi_id=poi_id,
        data=data,
        current_person=current_person,
    )

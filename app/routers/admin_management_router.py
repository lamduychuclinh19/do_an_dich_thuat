"""API quản lý tài khoản chủ địa điểm dành riêng cho SYSTEM_ADMIN."""

from fastapi import APIRouter, Depends, status

from app.dependencies.auth_dependency import require_system_admin
from app.schemas.admin_schema import (
    AdminAccountResponse,
    ResetPasswordResponse,
    ShopOwnerCreate,
    ShopOwnerUpdate,
)
from app.services.admin_management_service import (
    admin_management_service,
)


# Tất cả endpoint trong router này chỉ dành cho SYSTEM_ADMIN.
# Việc kiểm tra được thực hiện ở backend, nên SHOP_OWNER hoặc TOURIST
# nhập trực tiếp URL cũng vẫn bị chặn với mã 403.
router = APIRouter(
    prefix="/api/admin/shop-owners",
    tags=["SYSTEM ADMIN - Shop owners"],
)


@router.get(
    "",
    response_model=list[AdminAccountResponse],
)
def get_all_shop_owners(
    keyword: str | None = None,
    is_active: bool | None = None,
    current_admin: dict = Depends(require_system_admin),
):
    """Tìm SHOP_OWNER theo tên quán/SĐT và lọc trạng thái."""
    return admin_management_service.get_all_shop_owners(
        current_admin=current_admin,
        keyword=keyword,
        is_active=is_active,
    )


@router.get(
    "/{admin_id}",
    response_model=AdminAccountResponse,
)
def get_shop_owner_by_id(
    admin_id: int,
    current_admin: dict = Depends(require_system_admin),
):
    """Lấy chi tiết một tài khoản SHOP_OWNER."""
    return admin_management_service.get_shop_owner_by_id(
        admin_id=admin_id,
        current_admin=current_admin,
    )


@router.post(
    "",
    response_model=AdminAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shop_owner(
    data: ShopOwnerCreate,
    current_admin: dict = Depends(require_system_admin),
):
    """Cấp tài khoản SHOP_OWNER với mật khẩu mặc định abc12345."""
    return admin_management_service.create_shop_owner(
        data=data,
        current_admin=current_admin,
    )


@router.patch(
    "/{admin_id}",
    response_model=AdminAccountResponse,
)
def update_shop_owner(
    admin_id: int,
    data: ShopOwnerUpdate,
    current_admin: dict = Depends(require_system_admin),
):
    """Sửa thông tin và trạng thái của SHOP_OWNER trong cùng một API."""
    return admin_management_service.update_shop_owner(
        admin_id=admin_id,
        data=data,
        current_admin=current_admin,
    )


@router.post(
    "/{admin_id}/reset-password",
    response_model=ResetPasswordResponse,
)
def reset_shop_owner_password(
    admin_id: int,
    current_admin: dict = Depends(require_system_admin),
):
    """Đặt lại mật khẩu SHOP_OWNER về abc12345."""
    return admin_management_service.reset_shop_owner_password(
        admin_id=admin_id,
        current_admin=current_admin,
    )

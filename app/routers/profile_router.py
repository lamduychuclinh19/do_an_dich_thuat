"""API hồ sơ cá nhân; chỉ SHOP_OWNER đang đăng nhập được sử dụng."""

from fastapi import APIRouter, Depends

from app.dependencies.auth_dependency import require_shop_owner
from app.schemas.profile_schema import (
    ChangePasswordRequest,
    ProfileMessageResponse,
    ShopOwnerProfileResponse,
    ShopOwnerProfileUpdate,
)
from app.services.profile_service import profile_service


router = APIRouter(
    prefix="/api/profile",
    tags=["SHOP OWNER - Profile"],
)


@router.get(
    "/me",
    response_model=ShopOwnerProfileResponse,
)
def get_my_profile(
    current_person: dict = Depends(require_shop_owner),
):
    """Xem thông tin của chính tài khoản trong JWT."""
    return profile_service.get_my_profile(current_person)


@router.patch(
    "/me",
    response_model=ShopOwnerProfileResponse,
)
def update_my_profile(
    data: ShopOwnerProfileUpdate,
    current_person: dict = Depends(require_shop_owner),
):
    """Sửa họ tên, số điện thoại và email của chính SHOP_OWNER."""
    return profile_service.update_my_profile(data, current_person)


@router.patch(
    "/me/password",
    response_model=ProfileMessageResponse,
)
def change_my_password(
    data: ChangePasswordRequest,
    current_person: dict = Depends(require_shop_owner),
):
    """Đổi mật khẩu; service xác minh mật khẩu cũ và tạo hash mới."""
    return profile_service.change_my_password(data, current_person)

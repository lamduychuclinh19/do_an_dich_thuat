"""Các dependency xác thực và phân quyền dùng trong FastAPI router."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositaries.people_repository import people_repository
from app.services.auth_service import auth_service


# auto_error=False giúp mình tự trả thông báo tiếng Việt khi thiếu token.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_person(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> dict:
    """Lấy người đang đăng nhập từ Bearer JWT, chưa giới hạn vai trò."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bạn cần đăng nhập để sử dụng chức năng này",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kiểu xác thực phải là Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return auth_service.verify_access_token(credentials.credentials)


def _require_roles(*allowed_roles: str) -> Callable:
    """Tạo dependency chỉ cho phép các vai trò được truyền vào."""

    def role_checker(
        current_person: dict = Depends(get_current_person),
    ) -> dict:
        if current_person["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền sử dụng chức năng này",
            )

        return current_person

    return role_checker


# Chỉ quản trị viên hệ thống được quản lý danh sách chủ địa điểm.
require_system_admin = _require_roles("SYSTEM_ADMIN")

# Chỉ chủ địa điểm được quản lý POI, nội dung dịch và tạo audio.
require_shop_owner = _require_roles("SHOP_OWNER")

# Chỉ tài khoản khách du lịch đang hoạt động được qua dependency này.
require_tourist = _require_roles("TOURIST")

# Dùng cho các màn hình quản trị trong giai đoạn chuyển đổi router.
# Các router cụ thể sẽ được đổi sang require_system_admin hoặc
# require_shop_owner ở bước tiếp theo.
require_back_office = _require_roles("SYSTEM_ADMIN", "SHOP_OWNER")

# Tên cũ được giữ tạm thời để những router chưa sửa không bị lỗi import.
require_admin = require_back_office


def require_paid_tourist(
    current_person: dict = Depends(require_tourist),
) -> dict:
    """Chỉ cho TOURIST có giao dịch thành công và còn thời hạn truy cập."""
    has_access = people_repository.has_active_tourist_access(
        current_person["id"]
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Bạn chưa có gói sử dụng hoặc gói sử dụng đã hết hạn"
            ),
        )

    return current_person

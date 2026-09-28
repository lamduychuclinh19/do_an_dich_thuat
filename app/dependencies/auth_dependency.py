from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.services.auth_service import auth_service


# auto_error=False để mình tự viết thông báo lỗi
# rõ ràng bằng tiếng Việt.
bearer_scheme = HTTPBearer(
    auto_error=False
)


def require_admin(
    credentials: (
        HTTPAuthorizationCredentials | None
    ) = Depends(bearer_scheme),
) -> dict:
    """
    Dependency dành cho tất cả quản trị viên.

    Thực hiện:
    1. Kiểm tra có gửi token không.
    2. Kiểm tra đúng kiểu Bearer không.
    3. Giải mã JWT.
    4. Đọc lại tài khoản từ SQL.
    5. Kiểm tra tài khoản còn hoạt động không.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Bạn cần đăng nhập bằng "
                "tài khoản quản trị"
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kiểu xác thực phải là Bearer",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # verify_access_token() không chỉ giải mã JWT
    # mà còn đọc tài khoản hiện tại từ SQL.
    return auth_service.verify_access_token(
        credentials.credentials
    )


def require_owner(
    current_admin: dict = Depends(
        require_admin
    ),
) -> dict:
    """
    Dependency chỉ dành cho chủ quán.

    STAFF dù có JWT hợp lệ vẫn nhận lỗi 403
    nếu gọi trực tiếp API quản lý nhân sự.
    """
    if current_admin.get("role") != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Chỉ chủ quán mới được quyền "
                "truy cập chức năng quản lý nhân sự"
            ),
        )

    return current_admin
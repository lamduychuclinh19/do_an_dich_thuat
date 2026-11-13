from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Hệ thống mới có đúng hai nhóm tài khoản:
# SYSTEM_ADMIN: quản trị hệ thống và quản lý tài khoản chủ quán.
# SHOP_OWNER: chủ quán, quản lý POI và nội dung thuyết minh của mình.
AdminRole = Literal[
    "SYSTEM_ADMIN",
    "SHOP_OWNER",
]


class ShopOwnerCreate(BaseModel):
    """
    Dữ liệu quản trị hệ thống nhập khi cấp tài khoản
    mới cho một chủ quán.

    Giao diện không gửi password vì backend luôn đặt
    mật khẩu ban đầu là abc12345 rồi băm trước khi lưu.

    Giao diện cũng không gửi role vì mọi tài khoản được
    tạo từ chức năng này luôn là SHOP_OWNER. Nhờ vậy,
    người dùng không thể sửa request để tự tạo thêm
    tài khoản SYSTEM_ADMIN.

    Tên quán không nằm trong request này. Tên quán/địa điểm
    được lưu bằng pois.name sau khi POI được tạo và liên kết
    với tài khoản qua pois.owner_id.
    """

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    phone: str = Field(
        pattern=r"^0[0-9]{9}$",
        description=(
            "Số điện thoại Việt Nam gồm 10 chữ số"
        ),
    )

    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class ShopOwnerUpdate(BaseModel):
    """
    Thông tin quản trị hệ thống được phép chỉnh sửa
    đối với tài khoản chủ quán.

    Trạng thái hoạt động nằm ngay trong form sửa thông
    tin. Hệ thống không tạo nút hoặc API bật/tắt riêng.

    Không có trường role để ngăn việc biến SHOP_OWNER
    thành SYSTEM_ADMIN thông qua request cập nhật.

    Tên quán được sửa tại chức năng quản lý POI, không sửa
    trong chức năng quản lý tài khoản.
    """

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        pattern=r"^0[0-9]{9}$",
    )

    email: str | None = Field(
        default=None,
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )

    is_active: bool | None = None


class AdminAccountResponse(BaseModel):
    """
    Thông tin tài khoản được phép trả về giao diện.

    Schema này dùng được cho cả SYSTEM_ADMIN và
    SHOP_OWNER nhưng tuyệt đối không chứa password_hash.
    """

    id: int
    username: str

    # Các tài khoản cũ có thể chưa được cập nhật đủ
    # thông tin nên các trường này tạm thời cho phép None.
    full_name: str | None

    # Đây KHÔNG phải cột của bảng people. Repository tổng hợp trường
    # này từ pois.name thông qua quan hệ pois.owner_id = people.id để
    # giao diện quản lý có thể hiển thị tên địa điểm của SHOP_OWNER.
    shop_name: str | None
    phone: str | None
    email: str | None

    role: AdminRole
    is_active: bool
    must_change_password: bool

    last_login_at: datetime | None
    created_by_admin_id: int | None
    created_at: datetime


class ResetPasswordResponse(BaseModel):
    """
    Kết quả sau khi SYSTEM_ADMIN đặt lại mật khẩu của
    một SHOP_OWNER về mật khẩu ban đầu abc12345.
    """

    message: str


# Các alias dưới đây giúp service/router cũ vẫn import
# được tên trước đây trong lúc dự án đang được chuyển đổi.
# Khi đã sửa xong toàn bộ service và router, ta có thể
# đổi các import sang tên mới rồi xóa ba alias này.
AdminCreate = ShopOwnerCreate
AdminUpdate = ShopOwnerUpdate
AdminResponse = AdminAccountResponse
AdminResetPasswordResponse = ResetPasswordResponse

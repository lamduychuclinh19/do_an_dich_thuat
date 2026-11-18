from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Hệ thống hiện có hai loại quản trị viên:
# OWNER: chủ quán, được quyền quản lý nhân sự.
# STAFF: nhân viên quản trị do chủ quán cấp tài khoản.
AdminRole = Literal["OWNER", "STAFF"]


class AdminCreate(BaseModel):
    """
    Dữ liệu chủ quán nhập khi cấp tài khoản mới.

    Không nhận password từ giao diện vì tài khoản mới
    luôn dùng mật khẩu mặc định abc12345.

    Không nhận role vì tài khoản được tạo mới
    luôn là STAFF, không được phép tạo thêm OWNER.
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
        description="Số điện thoại Việt Nam gồm 10 chữ số",
    )

    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class AdminUpdate(BaseModel):
    """
    Những thông tin chủ quán được phép chỉnh sửa.

    Trạng thái hoạt động được đặt trong form sửa thông tin,
    không tạo API bật/tắt riêng bên ngoài.
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


class AdminResponse(BaseModel):
    """
    Thông tin được phép trả về cho giao diện.

    Tuyệt đối không đưa password_hash vào response.
    """

    id: int
    username: str

    # Cho phép None tạm thời vì tài khoản chủ quán cũ
    # có thể chưa được nhập đầy đủ thông tin.
    full_name: str | None
    phone: str | None
    email: str | None

    role: AdminRole
    is_active: bool
    must_change_password: bool

    last_login_at: datetime | None
    created_by_admin_id: int | None
    created_at: datetime


class AdminResetPasswordResponse(BaseModel):
    """
    Kết quả trả về sau khi chủ quán đặt lại mật khẩu
    của một nhân viên về mật khẩu mặc định.
    """

    message: str
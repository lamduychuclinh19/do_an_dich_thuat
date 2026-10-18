"""Schema cho SHOP_OWNER xem hồ sơ và tự đổi mật khẩu."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ShopOwnerProfileResponse(BaseModel):
    """Thông tin an toàn trả về giao diện, không chứa password_hash."""

    id: int
    username: str
    full_name: str | None
    shop_name: str | None
    phone: str | None
    email: str | None
    role: Literal["SHOP_OWNER"]
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime


class ShopOwnerProfileUpdate(BaseModel):
    """SHOP_OWNER chỉ được sửa ba trường thông tin cá nhân này."""

    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(
        pattern=r"^0[0-9]{9}$",
        description="Số điện thoại Việt Nam gồm 10 chữ số",
    )
    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )

    @field_validator("phone")
    @classmethod
    def validate_vietnam_mobile_prefix(cls, value: str) -> str:
        valid_prefixes = {
            "032", "033", "034", "035", "036", "037", "038", "039",
            "052", "055", "056", "058", "059",
            "070", "076", "077", "078", "079",
            "081", "082", "083", "084", "085", "086", "088", "089",
            "090", "091", "092", "093", "094", "096", "097", "098", "099",
        }
        if value[:3] not in valid_prefixes:
            raise ValueError("Đầu số này không thuộc các đầu số di động Việt Nam")
        return value


class ChangePasswordRequest(BaseModel):
    """Dữ liệu đổi mật khẩu; backend sẽ kiểm tra và tạo hash mới."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class ProfileMessageResponse(BaseModel):
    message: str

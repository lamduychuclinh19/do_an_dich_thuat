"""Quy tắc dữ liệu đăng ký chủ quán và kết quả xét duyệt."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OwnerRegistrationCreate(BaseModel):
    """Kiểm tra thông tin tài khoản chủ quán trước khi lưu phiếu."""
    username: str = Field(min_length=4, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(pattern=r"^0[0-9]{9}$")
    email: str = Field(min_length=6, max_length=255)

    @field_validator("phone")
    @classmethod
    def validate_vietnam_mobile_prefix(cls, value: str) -> str:
        """Chặn số điện thoại có đầu số không thuộc mạng di động Việt Nam."""
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

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Bắt buộc mật khẩu có độ dài tối thiểu, chữ và chữ số."""
        if not any(character.isalpha() for character in value) or not any(
            character.isdigit() for character in value
        ):
            raise ValueError("Mật khẩu cần ít nhất 8 ký tự, gồm cả chữ và số")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Chuẩn hóa email và chỉ chấp nhận địa chỉ Gmail hợp lệ."""
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Email không đúng định dạng")
        if not value.endswith("@gmail.com") or len(value.split("@", 1)[0]) < 2:
            raise ValueError("Email đăng ký phải là địa chỉ Gmail hợp lệ")
        return value


class OwnerRegistrationDecision(BaseModel):
    """Kiểm tra trạng thái duyệt và ghi chú xử lý."""
    status: int = Field(ge=0, le=1)
    admin_note: str = Field(min_length=1, max_length=2000)


class OwnerRegistrationRead(BaseModel):
    """Định dạng phiếu đăng ký trả về cho giao diện admin."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    phone: str
    email: str
    created_at: datetime
    reviewed_at: datetime | None
    status: int | None
    admin_note: str | None

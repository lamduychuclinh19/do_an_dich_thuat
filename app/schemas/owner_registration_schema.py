from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OwnerRegistrationCreate(BaseModel):
    username: str = Field(min_length=4, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(pattern=r"^0[0-9]{9}$")
    email: str = Field(min_length=6, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(character.isalpha() for character in value) or not any(
            character.isdigit() for character in value
        ):
            raise ValueError("Mật khẩu cần ít nhất 8 ký tự, gồm cả chữ và số")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Email không đúng định dạng")
        if not value.endswith("@gmail.com") or len(value.split("@", 1)[0]) < 2:
            raise ValueError("Email đăng ký phải là địa chỉ Gmail hợp lệ")
        return value


class OwnerRegistrationDecision(BaseModel):
    status: int = Field(ge=0, le=1)
    admin_note: str = Field(min_length=1, max_length=2000)


class OwnerRegistrationRead(BaseModel):
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

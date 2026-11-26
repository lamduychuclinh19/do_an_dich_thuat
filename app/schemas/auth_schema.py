"""Cấu trúc dữ liệu vào/ra cho đăng nhập và token truy cập."""

from pydantic import BaseModel, Field


class AdminLogin(BaseModel):
    """Kiểm tra thông tin đăng nhập do client gửi lên."""
    username: str = Field(min_length=4)
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    """Định dạng token và thông tin vai trò trả về sau đăng nhập."""
    access_token: str
    token_type: str = "bearer"
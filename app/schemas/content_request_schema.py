"""Cấu trúc request cho yêu cầu nội dung và quyết định kiểm duyệt."""

from typing import Literal

from pydantic import BaseModel, Field


class ContentRequestCreate(BaseModel):
    """Mô tả loại yêu cầu, hành động, POI và nội dung người gửi."""
    request_type: Literal["POI", "TRANSLATION"]
    action: Literal["CREATE", "UPDATE"]
    target_poi_id: str | None = Field(default=None, max_length=10)
    details: dict


class ContentRequestDecision(BaseModel):
    """Kiểm tra quyết định và ghi chú bắt buộc của admin."""
    approved: bool
    admin_note: str = Field(min_length=1, max_length=2000)


class NotificationRead(BaseModel):
    """Định dạng trạng thái đã đọc của thông báo."""
    is_read: bool = True

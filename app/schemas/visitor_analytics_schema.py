"""Schemas cho heartbeat khách ẩn danh và thống kê thiết bị."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class VisitorHeartbeatRequest(BaseModel):
    guest_session_id: UUID
    language_code: Literal["vi", "en", "fr", "zh", "ko"] = "en"


class VisitorDeviceSummary(BaseModel):
    device_type: str
    operating_system: str
    browser: str
    visitor_count: int


class VisitorAnalyticsResponse(BaseModel):
    active_visitors: int
    devices: list[VisitorDeviceSummary] = Field(default_factory=list)

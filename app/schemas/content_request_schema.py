from typing import Literal

from pydantic import BaseModel, Field


class ContentRequestCreate(BaseModel):
    request_type: Literal["POI", "TRANSLATION"]
    action: Literal["CREATE", "UPDATE"]
    target_poi_id: str | None = Field(default=None, max_length=10)
    details: dict


class ContentRequestDecision(BaseModel):
    approved: bool
    admin_note: str = Field(min_length=1, max_length=2000)


class NotificationRead(BaseModel):
    is_read: bool = True

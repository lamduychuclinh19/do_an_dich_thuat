"""Các schema cho nội dung thuyết minh đa ngôn ngữ."""

from typing import Literal

from pydantic import BaseModel, Field


LanguageCode = Literal["vi", "en", "fr", "zh", "ko"]


class TranslationSourceCreate(BaseModel):
    """Nội dung nguồn tiếng Việt do SHOP_OWNER nhập một lần."""

    poi_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    narration_text: str = Field(min_length=1, max_length=20_000)


class TranslationSourceUpdate(BaseModel):
    """Sửa nguồn tiếng Việt; backend sẽ tạo lại đủ năm ngôn ngữ."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    narration_text: str | None = Field(
        default=None,
        min_length=1,
        max_length=20_000,
    )


class TranslationCreate(BaseModel):
    """Schema nội bộ/ tương thích cho một bản ghi ngôn ngữ."""

    poi_id: int = Field(gt=0)
    language_code: LanguageCode
    title: str = Field(min_length=1, max_length=200)
    narration_text: str = Field(min_length=1, max_length=20_000)
    audio_url: str | None = None
    is_machine_generated: bool = True


class TranslationUpdate(BaseModel):
    """Giữ lại để những phần code cũ chưa chuyển đổi không lỗi import."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    narration_text: str | None = Field(
        default=None,
        min_length=1,
        max_length=20_000,
    )


class TranslationResponse(BaseModel):
    id: int
    poi_id: int
    language_code: LanguageCode
    title: str
    narration_text: str
    audio_url: str | None
    is_machine_generated: bool
    is_active: bool


class TranslationVisibility(BaseModel):
    is_active: bool

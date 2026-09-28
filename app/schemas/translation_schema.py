from typing import Literal

from pydantic import BaseModel, Field


# Các mã ngôn ngữ được hệ thống hỗ trợ.
LanguageCode = Literal[
    "vi",
    "en",
    "fr",
    "zh",
    "ko",
]


class TranslationCreate(BaseModel):
    """
    Dữ liệu admin nhập khi tạo một bản dịch.

    audio_url không được nhập trực tiếp ở đây.
    Sau khi tạo bản dịch, admin sẽ dùng API upload audio.
    """

    poi_id: int = Field(
        gt=0,
        description="ID của địa điểm cần thêm bản dịch",
    )

    language_code: LanguageCode

    title: str = Field(
        min_length=1,
        description="Tiêu đề theo ngôn ngữ đã chọn",
    )

    narration_text: str = Field(
        min_length=1,
        description="Nội dung dùng để thuyết minh",
    )


class TranslationUpdate(BaseModel):
    """
    Những nội dung admin được phép sửa.

    Không cho sửa audio_url tại đây vì file audio
    được quản lý bởi API upload riêng.
    """

    title: str | None = Field(
        default=None,
        min_length=1,
    )

    narration_text: str | None = Field(
        default=None,
        min_length=1,
    )


class TranslationResponse(BaseModel):
    """
    Dữ liệu hoàn chỉnh backend trả về.

    Khác TranslationCreate, response có audio_url
    vì đây là đường dẫn đã được backend quản lý.
    """

    id: int
    poi_id: int
    language_code: LanguageCode
    title: str
    narration_text: str
    audio_url: str | None
    is_active: bool


class TranslationVisibility(BaseModel):
    """
    Dữ liệu dùng để ẩn hoặc hiện một bản dịch.
    """

    is_active: bool
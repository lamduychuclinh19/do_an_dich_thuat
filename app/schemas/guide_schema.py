from typing import Literal

from pydantic import BaseModel


LanguageCode = Literal[
    "vi",
    "en",
    "fr",
    "zh",
    "ko",
]


class NearbyGuideResponse(BaseModel):
    poi_id: int
    poi_name: str
    address: str

    latitude: float
    longitude: float
    distance_meters: float

    language_code: LanguageCode

    title: str
    narration_text: str
    audio_url: str | None


class GuideItemResponse(BaseModel):
    poi_id: int
    poi_name: str
    address: str

    latitude: float
    longitude: float
    trigger_radius_meters: float

    # Ngôn ngữ khách yêu cầu
    requested_language_code: LanguageCode

    # Ngôn ngữ thực tế được trả về sau khi fallback
    language_code: LanguageCode

    title: str
    narration_text: str
    audio_url: str | None

    # True nếu không có ngôn ngữ yêu cầu và phải dùng en/vi
    is_fallback: bool = False
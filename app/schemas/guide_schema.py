from typing import Literal

from pydantic import BaseModel


class NearbyGuideResponse(BaseModel):
    poi_id: int
    poi_name: str
    address: str

    latitude: float
    longitude: float
    distance_meters: float

    language_code: Literal[
        "vi",
        "en",
        "fr",
        "zh",
        "ko",
    ]

    title: str
    narration_text: str
    audio_url: str | None
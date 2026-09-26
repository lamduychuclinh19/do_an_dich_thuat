from pydantic import BaseModel, Field
from typing import Literal

class TranslationCreate(BaseModel):
    poi_id: int = Field(gt=0)

    language_code: Literal[
    "vi",
    "en",
    "fr",
    "zh",
    "ko"
    ]

    title: str = Field(min_length=1)
    narration_text: str = Field(min_length=1)

    audio_url: str | None = None

class TranslationUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
    )

    narration_text: str | None = Field(
        default=None,
        min_length=1,
    )

    audio_url: str | None = None

class TranslationResponse(TranslationCreate):
    id: int
    is_active: bool
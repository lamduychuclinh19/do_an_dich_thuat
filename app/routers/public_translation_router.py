from typing import Literal

from fastapi import APIRouter

from app.schemas.translation_schema import TranslationResponse
from app.services.translation_service import translation_service


router = APIRouter(
    prefix="/api/public/translations",
    tags=["PUBLIC - Translations"],
)


@router.get(
    "/poi/{poi_id}",
    response_model=list[TranslationResponse],
)
def get_all_translations(poi_id: int):
    return translation_service.get_all_translations(
        poi_id,
    )


@router.get(
    "/poi/{poi_id}/{language_code}",
    response_model=TranslationResponse,
)
def get_translation(
    poi_id: int,
    language_code: Literal[
        "vi",
        "en",
        "fr",
        "zh",
        "ko",
    ],
):
    return translation_service.get_translation(
        poi_id,
        language_code,
    )
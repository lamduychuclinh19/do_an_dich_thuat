from fastapi import APIRouter, Depends, File, UploadFile
from app.dependencies.auth_dependency import require_admin
from app.schemas.translation_schema import (
    TranslationCreate,
    TranslationResponse,
    TranslationUpdate,
)
from app.services.translation_service import (
    translation_service
)


router = APIRouter(
    prefix="/api/translations",
    tags=["Translations"]
)


@router.post(
    "",
    response_model=TranslationResponse,
    dependencies=[Depends(require_admin)],
)
def create_translation(data: TranslationCreate):
    return translation_service.create_translation(data)


@router.get(
    "/poi/{poi_id}",
    response_model=list[TranslationResponse]
)
def get_all_translations(poi_id: int):
    return translation_service.get_all_translations(
        poi_id
    )


@router.get(
    "/poi/{poi_id}/{language_code}",
    response_model=TranslationResponse
)
def get_translation(
    poi_id: int,
    language_code: str
):
    return translation_service.get_translation(
        poi_id,
        language_code
    )


@router.patch(
    "/{translation_id}",
    response_model=TranslationResponse,
    dependencies=[Depends(require_admin)],
)
def update_translation(
    translation_id: int,
    data: TranslationUpdate,
): 
    return translation_service.update_translation(
        translation_id,
        data,
    )

@router.post(
    "/{translation_id}/audio",
    response_model=TranslationResponse,
    dependencies=[Depends(require_admin)],
)
async def upload_translation_audio(
    translation_id: int,
    audio_file: UploadFile = File(...),
):
    return (
        await translation_service.upload_translation_audio(
            translation_id,
            audio_file,
        )
    )
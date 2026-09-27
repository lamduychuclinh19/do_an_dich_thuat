from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    status,
)
from app.schemas.translation_schema import TranslationVisibility
from app.dependencies.auth_dependency import require_admin
from app.schemas.translation_schema import (
    TranslationCreate,
    TranslationResponse,
    TranslationUpdate,
)
from app.services.translation_service import translation_service


router = APIRouter(
    prefix="/api/admin/translations",
    tags=["ADMIN - Translations"],
    dependencies=[Depends(require_admin)],
)

@router.get(
    "/poi/{poi_id}",
    response_model=list[TranslationResponse],
)
def get_all_translations_for_admin(poi_id: int,):
    return translation_service.get_all_translations_for_admin(
        poi_id,
    )

@router.post(
    "",
    response_model=TranslationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_translation(data: TranslationCreate):
    return translation_service.create_translation(data)


@router.patch(
    "/{translation_id}",
    response_model=TranslationResponse,
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
)
async def upload_translation_audio(
    translation_id: int,
    audio_file: UploadFile = File(...),
):
    return await translation_service.upload_translation_audio(
        translation_id,
        audio_file,
    )
@router.patch(
    "/{translation_id}/visibility",
    response_model=TranslationResponse,
)
def set_translation_visibility(
    translation_id: int,
    data: TranslationVisibility,
):
    return translation_service.set_translation_visibility(
        translation_id,
        data.is_active,
    )
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    status,
)

from app.dependencies.auth_dependency import require_admin
from app.schemas.translation_schema import (
    LanguageCode,
    TranslationCreate,
    TranslationResponse,
    TranslationUpdate,
    TranslationVisibility,
)
from app.services.translation_service import (
    translation_service,
)


# Toàn bộ API trong router này chỉ dành cho admin.
router = APIRouter(
    prefix="/api/admin/translations",
    tags=["ADMIN - Translations"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "/poi/{poi_id}",
    response_model=list[TranslationResponse],
)
def get_all_translations_for_admin(
    poi_id: int,
):
    """
    Lấy tất cả bản dịch của POI.

    Admin nhìn thấy cả bản dịch đang hoạt động
    và bản dịch đang bị ẩn.
    """

    return (
        translation_service
        .get_all_translations_for_admin(poi_id)
    )


@router.post(
    "",
    response_model=TranslationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_translation(
    data: TranslationCreate,
):
    """
    Tạo bản dịch bằng dữ liệu JSON.

    Backend tự chuyển narration_text thành MP3,
    admin không cần cung cấp audio_url.
    """

    return await translation_service.create_translation(
        data
    )


@router.post(
    "/from-text-file",
    response_model=TranslationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_translation_from_text_file(
    poi_id: int = Form(
        ...,
        gt=0,
    ),
    language_code: LanguageCode = Form(...),
    title: str = Form(
        ...,
        min_length=1,
    ),
    text_file: UploadFile = File(...),
):
    """
    Tạo bản dịch từ file TXT UTF-8.

    Nội dung file trở thành narration_text,
    sau đó backend tự tạo file MP3.
    """

    return await (
        translation_service
        .create_translation_from_text_file(
            poi_id=poi_id,
            language_code=language_code,
            title=title,
            text_file=text_file,
        )
    )


@router.patch(
    "/{translation_id}",
    response_model=TranslationResponse,
)
async def update_translation(
    translation_id: int,
    data: TranslationUpdate,
):
    """
    Cập nhật bản dịch bằng JSON.

    Nếu narration_text thay đổi,
    backend tự sinh lại audio.
    """

    return await translation_service.update_translation(
        translation_id=translation_id,
        data=data,
    )


@router.patch(
    "/{translation_id}/from-text-file",
    response_model=TranslationResponse,
)
async def update_translation_from_text_file(
    translation_id: int,
    text_file: UploadFile = File(...),
    title: str | None = Form(default=None),
):
    """
    Thay nội dung thuyết minh bằng file TXT mới.

    Backend đọc file, cập nhật narration_text,
    tạo MP3 mới rồi mới xóa MP3 cũ.
    """

    return await (
        translation_service
        .update_translation_from_text_file(
            translation_id=translation_id,
            text_file=text_file,
            title=title,
        )
    )


@router.post(
    "/{translation_id}/regenerate-audio",
    response_model=TranslationResponse,
)
async def regenerate_translation_audio(
    translation_id: int,
):
    """
    Tạo lại MP3 từ narration_text đang có trong SQL.

    Dùng khi audio cũ bị lỗi hoặc cần tạo lại giọng đọc.
    """

    return await (
        translation_service
        .regenerate_translation_audio(
            translation_id
        )
    )


@router.patch(
    "/{translation_id}/visibility",
    response_model=TranslationResponse,
)
def set_translation_visibility(
    translation_id: int,
    data: TranslationVisibility,
):
    """
    Ẩn hoặc hiện bản dịch.

    Việc ẩn không xóa narration_text và file MP3.
    """

    return (
        translation_service
        .set_translation_visibility(
            translation_id,
            data.is_active,
        )
    )
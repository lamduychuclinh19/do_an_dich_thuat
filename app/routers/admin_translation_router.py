"""API quản trị Translation dùng chung cho SYSTEM_ADMIN và SHOP_OWNER."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies.auth_dependency import require_back_office
from app.schemas.translation_schema import (
    TranslationResponse,
    TranslationSourceCreate,
    TranslationSourceUpdate,
    TranslationVisibility,
)
from app.services.translation_service import translation_service


router = APIRouter(
    prefix="/api/admin/translations",
    tags=["BACK OFFICE - Translations"],
)


def _require_review_request() -> None:
    raise HTTPException(status_code=403, detail="Tạo/cập nhật bản dịch và audio phải gửi yêu cầu để SYSTEM_ADMIN duyệt.")


@router.get(
    "/poi/{poi_id}",
    response_model=list[TranslationResponse],
)
def get_all_translations_for_back_office(
    poi_id: str,
    current_person: dict = Depends(require_back_office),
):
    """SYSTEM_ADMIN xem mọi POI; SHOP_OWNER chỉ xem POI của mình."""
    return translation_service.get_all_translations_for_back_office(
        poi_id=poi_id,
        current_person=current_person,
    )


@router.post(
    "/from-vietnamese",
    response_model=list[TranslationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_from_vietnamese(
    data: TranslationSourceCreate,
    current_person: dict = Depends(require_back_office),
):
    """Nhập một nội dung Việt và tự tạo năm ngôn ngữ cùng năm audio."""
    _require_review_request()


@router.post(
    "/from-vietnamese-text-file",
    response_model=list[TranslationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_from_vietnamese_text_file(
    poi_id: str = Form(..., min_length=1, max_length=10),
    title: str = Form(..., min_length=1, max_length=200),
    text_file: UploadFile = File(...),
    current_person: dict = Depends(require_back_office),
):
    """Tải một file TXT tiếng Việt và tự tạo đủ năm ngôn ngữ/audio."""
    _require_review_request()


@router.patch(
    "/poi/{poi_id}/source",
    response_model=list[TranslationResponse],
)
async def update_vietnamese_source(
    poi_id: str,
    data: TranslationSourceUpdate,
    current_person: dict = Depends(require_back_office),
):
    """Sửa nguồn Việt rồi tự tạo lại bản dịch và audio của cả năm ngôn ngữ."""
    _require_review_request()


@router.patch(
    "/poi/{poi_id}/source/from-text-file",
    response_model=list[TranslationResponse],
)
async def update_vietnamese_source_from_text_file(
    poi_id: str,
    text_file: UploadFile = File(...),
    title: str | None = Form(default=None, max_length=200),
    current_person: dict = Depends(require_back_office),
):
    """Thay nguồn Việt bằng TXT rồi tự tạo lại đủ năm ngôn ngữ/audio."""
    _require_review_request()


@router.post(
    "/{translation_id}/regenerate-audio",
    response_model=TranslationResponse,
)
async def regenerate_translation_audio(
    translation_id: int,
    current_person: dict = Depends(require_back_office),
):
    """Tạo lại MP3 sau khi service kiểm tra vai trò và quyền sở hữu."""
    _require_review_request()


@router.patch(
    "/{translation_id}/visibility",
    response_model=TranslationResponse,
)
def set_translation_visibility(
    translation_id: int,
    data: TranslationVisibility,
    current_person: dict = Depends(require_back_office),
):
    """Ẩn/hiện bản dịch theo quyền, không xóa dữ liệu hoặc audio."""
    return translation_service.set_visibility_for_back_office(
        translation_id=translation_id,
        is_active=data.is_active,
        current_person=current_person,
    )

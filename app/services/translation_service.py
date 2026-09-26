from fastapi import (HTTPException,UploadFile,status,)
from app.repositaries.poi_repository import poi_repository
from app.repositaries.translation_repository import (
    translation_repository
)
from app.schemas.translation_schema import (TranslationCreate,TranslationUpdate,)
from app.services.audio_service import audio_service

class TranslationService:
    def create_translation(
        self,
        data: TranslationCreate
    ) -> dict:
        poi = poi_repository.get_by_id(data.poi_id)

        if poi is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found"
            )

        existing_translation = (
            translation_repository.get_by_poi_and_language(
                data.poi_id,
                data.language_code
            )
        )

        if existing_translation is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Translation already exists"
            )

        return translation_repository.create(
            data.model_dump()
        )

    def get_translation(self,poi_id: int,language_code: str) -> dict:
        poi = poi_repository.get_by_id(poi_id)

        if poi is None or poi["is_active"] is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found"
            )

        translation = (
            translation_repository.get_by_poi_and_language(
                poi_id,
                language_code
            )
        )

        if translation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found"
            )

        return translation

    def get_all_translations(self,poi_id: int) -> list:
        poi = poi_repository.get_by_id(poi_id)

        if poi is None or poi["is_active"] is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found"
            )

        return translation_repository.get_all_by_poi(
            poi_id
        )
    def update_translation(
        self,
        translation_id: int,
        data: TranslationUpdate,
    ) -> dict:
        existing_translation = (
            translation_repository.get_by_id(
                translation_id
            )
        )

        if existing_translation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found",
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields were provided for update",
            )

        updated_translation = (
            translation_repository.update(
                translation_id,
                update_data,
            )
        )

        return updated_translation
    
    async def upload_translation_audio(
        self,
        translation_id: int,
        audio_file: UploadFile,
    ) -> dict:
        existing_translation = (
            translation_repository.get_by_id(
                translation_id
            )
        )

        if existing_translation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found",
            )

        old_audio_url = existing_translation.get(
            "audio_url"
        )

        new_audio_url = await audio_service.save_audio(
            audio_file
        )

        try:
            updated_translation = (
                translation_repository.update(
                    translation_id,
                    {
                        "audio_url": new_audio_url
                    },
                )
            )
        except Exception:
            # Nếu cập nhật SQL thất bại thì xóa file vừa lưu,
            # tránh để lại file rác.
            audio_service.delete_audio(
                new_audio_url
            )
            raise

        # Chỉ xóa file cũ sau khi SQL cập nhật thành công.
        if old_audio_url != new_audio_url:
            audio_service.delete_audio(
                old_audio_url
            )

        return updated_translation

translation_service = TranslationService()
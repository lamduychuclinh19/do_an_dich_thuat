from fastapi import (
    HTTPException,
    UploadFile,
    status,
)

from app.repositaries.poi_repository import (
    poi_repository,
)
from app.repositaries.translation_repository import (
    translation_repository,
)
from app.schemas.translation_schema import (
    TranslationCreate,
    TranslationUpdate,
)
from app.services.audio_service import audio_service


class TranslationService:
    def _get_translation_or_404(
        self,
        translation_id: int,
    ) -> dict:
        """
        Hàm hỗ trợ dùng chung để tìm bản dịch theo ID.
        """

        translation = translation_repository.get_by_id(
            translation_id
        )

        if translation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found",
            )

        return translation

    def _check_duplicate_language(
        self,
        poi_id: int,
        language_code: str,
    ) -> None:
        """
        Không cho một POI có hai bản dịch cùng ngôn ngữ,
        kể cả khi một bản dịch đang bị ẩn.
        """

        translations = (
            translation_repository
            .get_all_for_admin_by_poi(poi_id)
        )

        already_exists = any(
            item["language_code"] == language_code
            for item in translations
        )

        if already_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Translation already exists. "
                    "Reactivate the existing translation "
                    "instead of creating a duplicate."
                ),
            )

    async def create_translation(
        self,
        data: TranslationCreate,
    ) -> dict:
        """
        Tạo bản dịch và tự sinh file MP3.

        Trình tự:
        1. Kiểm tra POI.
        2. Kiểm tra trùng ngôn ngữ.
        3. Sinh MP3 từ narration_text.
        4. Lưu bản dịch và audio_url vào SQL.
        """

        poi = poi_repository.get_by_id(data.poi_id)

        if poi is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found",
            )

        self._check_duplicate_language(
            poi_id=data.poi_id,
            language_code=data.language_code,
        )

        # Sinh audio trước khi ghi SQL.
        # Nếu Edge-TTS lỗi thì database chưa bị thay đổi.
        audio_url = await audio_service.generate_audio(
            text=data.narration_text,
            language_code=data.language_code,
        )

        create_data = data.model_dump()
        create_data["audio_url"] = audio_url

        try:
            return translation_repository.create(
                create_data
            )
        except Exception:
            # SQL lỗi thì xóa MP3 vừa tạo để tránh file rác.
            audio_service.delete_audio(audio_url)
            raise

    async def create_translation_from_text_file(
        self,
        poi_id: int,
        language_code: str,
        title: str,
        text_file: UploadFile,
    ) -> dict:
        """
        Tạo bản dịch từ file TXT do admin tải lên.

        Nội dung file trở thành narration_text,
        sau đó luồng xử lý giống create_translation().
        """

        narration_text = (
            await audio_service.read_text_file(
                text_file
            )
        )

        translation_data = TranslationCreate(
            poi_id=poi_id,
            language_code=language_code,
            title=title,
            narration_text=narration_text,
        )

        return await self.create_translation(
            translation_data
        )

    def get_translation(
        self,
        poi_id: int,
        language_code: str,
    ) -> dict:
        """
        Lấy một bản dịch công khai.

        POI bị ẩn hoặc bản dịch bị ẩn sẽ không được trả ra.
        """

        poi = poi_repository.get_by_id(poi_id)

        if poi is None or poi["is_active"] is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found",
            )

        translation = (
            translation_repository
            .get_by_poi_and_language(
                poi_id,
                language_code,
            )
        )

        if translation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found",
            )

        return translation

    def get_all_translations(
        self,
        poi_id: int,
    ) -> list:
        """
        Lấy các bản dịch đang hiển thị của một POI.
        """

        poi = poi_repository.get_by_id(poi_id)

        if poi is None or poi["is_active"] is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found",
            )

        return translation_repository.get_all_by_poi(
            poi_id
        )

    async def update_translation(
        self,
        translation_id: int,
        data: TranslationUpdate,
    ) -> dict:
        """
        Cập nhật bản dịch.

        Nếu narration_text thay đổi:
        - Sinh MP3 mới trước.
        - Cập nhật text và audio_url cùng lúc trong SQL.
        - SQL thành công mới xóa MP3 cũ.

        Nếu chỉ sửa title thì giữ nguyên audio.
        """

        existing_translation = (
            self._get_translation_or_404(
                translation_id
            )
        )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields were provided for update",
            )

        narration_changed = (
            "narration_text" in update_data
            and update_data["narration_text"]
            != existing_translation["narration_text"]
        )

        old_audio_url = existing_translation.get(
            "audio_url"
        )
        new_audio_url = None

        if narration_changed:
            # Sinh audio mới trước khi thay đổi database.
            new_audio_url = (
                await audio_service.generate_audio(
                    text=update_data["narration_text"],
                    language_code=(
                        existing_translation[
                            "language_code"
                        ]
                    ),
                )
            )

            update_data["audio_url"] = new_audio_url

        try:
            updated_translation = (
                translation_repository.update(
                    translation_id,
                    update_data,
                )
            )

            if updated_translation is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail="Translation not found",
                )

        except Exception:
            # SQL thất bại thì xóa audio mới,
            # giữ nguyên audio cũ và dữ liệu cũ.
            if new_audio_url:
                audio_service.delete_audio(
                    new_audio_url
                )
            raise

        # Chỉ xóa audio cũ sau khi SQL thành công.
        if narration_changed and old_audio_url:
            audio_service.delete_audio(
                old_audio_url
            )

        return updated_translation

    async def update_translation_from_text_file(
        self,
        translation_id: int,
        text_file: UploadFile,
        title: str | None = None,
    ) -> dict:
        """
        Cập nhật nội dung từ file TXT.

        File TXT thay thế narration_text hiện tại
        và hệ thống tự sinh lại MP3.
        """

        narration_text = (
            await audio_service.read_text_file(
                text_file
            )
        )

        update_data = TranslationUpdate(
            title=title,
            narration_text=narration_text,
        )

        return await self.update_translation(
            translation_id=translation_id,
            data=update_data,
        )

    async def regenerate_translation_audio(
        self,
        translation_id: int,
    ) -> dict:
        """
        Tạo lại audio từ narration_text đang lưu trong SQL.

        Chức năng này hữu ích nếu lần tạo trước thất bại
        hoặc admin muốn đổi lại giọng đọc sau này.
        """

        existing_translation = (
            self._get_translation_or_404(
                translation_id
            )
        )

        old_audio_url = existing_translation.get(
            "audio_url"
        )

        new_audio_url = (
            await audio_service.generate_audio(
                text=existing_translation[
                    "narration_text"
                ],
                language_code=existing_translation[
                    "language_code"
                ],
            )
        )

        try:
            updated_translation = (
                translation_repository.update(
                    translation_id,
                    {"audio_url": new_audio_url},
                )
            )

            if updated_translation is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail="Translation not found",
                )

        except Exception:
            audio_service.delete_audio(new_audio_url)
            raise

        # SQL đã trỏ tới file mới thì mới xóa file cũ.
        if old_audio_url != new_audio_url:
            audio_service.delete_audio(old_audio_url)

        return updated_translation

    def get_all_translations_for_admin(
        self,
        poi_id: int,
    ) -> list:
        """
        Admin nhìn thấy cả bản dịch đang hiện và đang ẩn.
        """

        poi = poi_repository.get_by_id(poi_id)

        if poi is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found",
            )

        return (
            translation_repository
            .get_all_for_admin_by_poi(poi_id)
        )

    def set_translation_visibility(
        self,
        translation_id: int,
        is_active: bool,
    ) -> dict:
        """
        Ẩn hoặc hiện bản dịch.

        Việc ẩn không xóa MP3 để khi hiện lại
        không cần tạo audio thêm lần nữa.
        """

        updated_translation = (
            translation_repository.set_visibility(
                translation_id,
                is_active,
            )
        )

        if updated_translation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found",
            )

        return updated_translation


translation_service = TranslationService()
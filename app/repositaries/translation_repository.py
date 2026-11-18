from sqlalchemy import text
from app.database import engine


class TranslationRepository:
    def _convert_row_to_dict(self, row) -> dict | None:
        if row is None:
            return None

        translation = dict(row)
        translation["is_active"] = bool(
            translation["is_active"]
        )

        return translation

    def create(self, data: dict) -> dict:
        query = text(
            """
            INSERT INTO dbo.translations
            (
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_active
            )
            OUTPUT
                INSERTED.id,
                INSERTED.poi_id,
                INSERTED.language_code,
                INSERTED.title,
                INSERTED.narration_text,
                INSERTED.audio_url,
                INSERTED.is_active
            VALUES
            (
                :poi_id,
                :language_code,
                :title,
                :narration_text,
                :audio_url,
                1
            )
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                data,
            ).mappings().one()

        return self._convert_row_to_dict(row)

    def get_by_poi_and_language(
        self,
        poi_id: int,
        language_code: str,
    ) -> dict | None:
        query = text(
            """
            SELECT
                id,
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_active
            FROM dbo.translations
            WHERE poi_id = :poi_id
              AND language_code = :language_code
              AND is_active = 1
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {
                    "poi_id": poi_id,
                    "language_code": language_code,
                },
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def get_all_by_poi(self, poi_id: int) -> list[dict]:
        query = text(
            """
            SELECT
                id,
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_active
            FROM dbo.translations
            WHERE poi_id = :poi_id
              AND is_active = 1
            ORDER BY language_code
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                {"poi_id": poi_id},
            ).mappings().all()

        return [
            self._convert_row_to_dict(row)
            for row in rows
        ]
    def get_by_id(
        self,
        translation_id: int,
    ) -> dict | None:
        query = text(
            """
            SELECT
                id,
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_active
            FROM dbo.translations
            WHERE id = :translation_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"translation_id": translation_id},
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def update(self,translation_id: int,data: dict,) -> dict | None:
        allowed_fields = {
            "title",
            "narration_text",
            "audio_url",
        }

        fields_to_update = [
            field
            for field in data
            if field in allowed_fields
        ]

        if not fields_to_update:
            return self.get_by_id(translation_id)

        set_statements = [
            f"{field} = :{field}"
            for field in fields_to_update
        ]

        set_statements.append(
            "updated_at = SYSUTCDATETIME()"
        )

        query = text(
            f"""
            UPDATE dbo.translations
            SET {", ".join(set_statements)}
            OUTPUT
                INSERTED.id,
                INSERTED.poi_id,
                INSERTED.language_code,
                INSERTED.title,
                INSERTED.narration_text,
                INSERTED.audio_url,
                INSERTED.is_active
            WHERE id = :translation_id
            """
        )

        parameters = {
            **data,
            "translation_id": translation_id,
        }

        with engine.begin() as connection:
            row = connection.execute(
                query,
                parameters,
            ).mappings().first()

        return self._convert_row_to_dict(row)
    def get_all_for_admin_by_poi(self,poi_id: int,) -> list:
        query = text(
            """
            SELECT
                id,
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_active
            FROM dbo.translations
            WHERE poi_id = :poi_id
            ORDER BY language_code
            """
        )

        with engine.connect() as connection:
            result = connection.execute(
                query,
                {"poi_id": poi_id},
            )

            return [
                dict(row)
                for row in result.mappings().all()
            ]

    def set_visibility(self,translation_id: int,is_active: bool,) -> dict | None:
        query = text(
            """
            UPDATE dbo.translations
            SET
                is_active = :is_active,
                updated_at = SYSUTCDATETIME()
            OUTPUT
                INSERTED.id,
                INSERTED.poi_id,
                INSERTED.language_code,
                INSERTED.title,
                INSERTED.narration_text,
                INSERTED.audio_url,
                INSERTED.is_active
            WHERE id = :translation_id
            """
        )

        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "translation_id": translation_id,
                    "is_active": is_active,
                },
            )

            row = result.mappings().first()

            if row is None:
                return None

            return dict(row)
    def get_public_guides(
        self,
        requested_language_code: str,
    ) -> list[dict]:
        """
        Lấy nội dung thuyết minh của tất cả POI đang hiển thị.

        Thứ tự ưu tiên ngôn ngữ:
        1. Ngôn ngữ khách yêu cầu.
        2. Tiếng Anh nếu chưa có ngôn ngữ yêu cầu.
        3. Tiếng Việt nếu cũng chưa có tiếng Anh.

        POI bị ẩn hoặc bản dịch bị ẩn sẽ không được trả ra.
        """

        query = text(
            """
            SELECT
                p.id AS poi_id,
                p.name AS poi_name,
                p.address,
                p.latitude,
                p.longitude,
                p.trigger_radius_meters,

                :requested_language_code
                    AS requested_language_code,

                selected_translation.language_code,
                selected_translation.title,
                selected_translation.narration_text,
                selected_translation.audio_url,

                CASE
                    WHEN selected_translation.language_code
                         = :requested_language_code
                    THEN CAST(0 AS BIT)
                    ELSE CAST(1 AS BIT)
                END AS is_fallback

            FROM dbo.pois AS p

            OUTER APPLY
            (
                /*
                Tìm một bản dịch phù hợp nhất cho từng POI.

                TOP 1 kết hợp ORDER BY sẽ ưu tiên:
                - Ngôn ngữ khách yêu cầu.
                - Sau đó là tiếng Anh.
                - Cuối cùng là tiếng Việt.
                */
                SELECT TOP 1
                    t.language_code,
                    t.title,
                    t.narration_text,
                    t.audio_url
                FROM dbo.translations AS t
                WHERE t.poi_id = p.id
                  AND t.is_active = 1
                  AND t.language_code IN
                  (
                      :requested_language_code,
                      'en',
                      'vi'
                  )
                ORDER BY
                    CASE
                        WHEN t.language_code
                             = :requested_language_code
                        THEN 1
                        WHEN t.language_code = 'en'
                        THEN 2
                        WHEN t.language_code = 'vi'
                        THEN 3
                        ELSE 4
                    END
            ) AS selected_translation

            WHERE p.is_active = 1

              /*
              Nếu POI không có cả ngôn ngữ yêu cầu,
              tiếng Anh lẫn tiếng Việt thì không trả POI đó.
              */
              AND selected_translation.language_code IS NOT NULL

            ORDER BY p.id
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                {
                    "requested_language_code":
                        requested_language_code,
                },
            ).mappings().all()

        guides = []

        for row in rows:
            guide = dict(row)

            # SQL Server trả BIT; chuyển về bool Python
            # để FastAPI xuất true/false đúng chuẩn JSON.
            guide["is_fallback"] = bool(
                guide["is_fallback"]
            )

            guides.append(guide)

        return guides        
translation_repository = TranslationRepository()
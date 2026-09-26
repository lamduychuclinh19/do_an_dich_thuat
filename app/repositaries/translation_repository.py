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

translation_repository = TranslationRepository()
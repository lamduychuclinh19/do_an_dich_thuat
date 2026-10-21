"""Repository SQL Server cho bảng translations, có kiểm tra owner_id."""

from sqlalchemy import text

from app.database import engine


class TranslationRepository:
    """Truy cập nội dung thuyết minh và cô lập dữ liệu giữa các chủ quán."""

    SELECT_COLUMNS = """
        translation.id,
        translation.poi_id,
        translation.language_code,
        translation.title,
        translation.narration_text,
        translation.audio_url,
        translation.is_machine_generated,
        translation.is_active,
        translation.created_at,
        translation.updated_at
    """

    @staticmethod
    def _row_to_dict(row) -> dict | None:
        if row is None:
            return None

        translation = dict(row)
        translation["is_machine_generated"] = bool(
            translation["is_machine_generated"]
        )
        translation["is_active"] = bool(translation["is_active"])
        return translation

    def get_by_poi_and_language(
        self,
        poi_id: int,
        language_code: str,
    ) -> dict | None:
        """Public chỉ lấy bản dịch đang hoạt động."""
        query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.poi_id = :poi_id
              AND translation.language_code = :language_code
              AND translation.is_active = 1
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

        return self._row_to_dict(row)

    def get_all_by_poi(self, poi_id: int) -> list[dict]:
        """Public chỉ thấy các ngôn ngữ đang hoạt động."""
        query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.poi_id = :poi_id
              AND translation.is_active = 1
            ORDER BY translation.language_code
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                {"poi_id": poi_id},
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def get_by_id_for_owner(
        self,
        translation_id: int,
        owner_id: int,
    ) -> dict | None:
        """Chỉ trả bản dịch nếu POI của nó thuộc đúng SHOP_OWNER."""
        query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.id = :translation_id
              AND poi.owner_id = :owner_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {
                    "translation_id": translation_id,
                    "owner_id": owner_id,
                },
            ).mappings().first()

        return self._row_to_dict(row)

    def get_by_id_for_system_admin(
        self,
        translation_id: int,
    ) -> dict | None:
        """SYSTEM_ADMIN được tìm bản dịch thuộc bất kỳ POI nào."""
        query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.id = :translation_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"translation_id": translation_id},
            ).mappings().first()

        return self._row_to_dict(row)

    def get_all_for_owner_by_poi(
        self,
        poi_id: int,
        owner_id: int,
    ) -> list[dict]:
        """SHOP_OWNER thấy cả bản dịch đang hiện và đang ẩn của POI mình."""
        query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.poi_id = :poi_id
              AND poi.owner_id = :owner_id
            ORDER BY translation.language_code
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                {
                    "poi_id": poi_id,
                    "owner_id": owner_id,
                },
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def get_all_for_system_admin_by_poi(
        self,
        poi_id: int,
    ) -> list[dict]:
        """SYSTEM_ADMIN thấy cả bản dịch đang hiện và đang ẩn của POI."""
        query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.poi_id = :poi_id
            ORDER BY translation.language_code
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                {"poi_id": poi_id},
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def create_many_for_owner(
        self,
        records: list[dict],
        owner_id: int,
    ) -> list[dict] | None:
        """Tạo đủ năm ngôn ngữ trong cùng một transaction SQL."""
        if not records:
            return []

        poi_id = records[0]["poi_id"]
        owner_query = text(
            """
            SELECT 1
            FROM dbo.pois
            WHERE id = :poi_id
              AND owner_id = :owner_id
            """
        )
        insert_query = text(
            """
            INSERT INTO dbo.translations
            (
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_machine_generated,
                is_active
            )
            VALUES
            (
                :poi_id,
                :language_code,
                :title,
                :narration_text,
                :audio_url,
                :is_machine_generated,
                1
            )
            """
        )
        select_query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.poi_id = :poi_id
              AND poi.owner_id = :owner_id
            ORDER BY translation.language_code
            """
        )

        with engine.begin() as connection:
            owns_poi = connection.execute(
                owner_query,
                {"poi_id": poi_id, "owner_id": owner_id},
            ).first()

            if owns_poi is None:
                return None

            for record in records:
                connection.execute(insert_query, record)

            rows = connection.execute(
                select_query,
                {"poi_id": poi_id, "owner_id": owner_id},
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def create_many_as_system_admin(
        self,
        records: list[dict],
    ) -> list[dict] | None:
        """SYSTEM_ADMIN tạo năm bản dịch cho một POI bất kỳ.

        Repository vẫn kiểm tra POI tồn tại trước khi INSERT để tránh tạo
        nội dung mồ côi nếu client gửi một ``poi_id`` không hợp lệ.
        """
        if not records:
            return []

        poi_id = records[0]["poi_id"]
        poi_query = text(
            """
            SELECT 1
            FROM dbo.pois
            WHERE id = :poi_id
            """
        )
        insert_query = text(
            """
            INSERT INTO dbo.translations
            (
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_machine_generated,
                is_active
            )
            VALUES
            (
                :poi_id,
                :language_code,
                :title,
                :narration_text,
                :audio_url,
                :is_machine_generated,
                1
            )
            """
        )
        select_query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.poi_id = :poi_id
            ORDER BY translation.language_code
            """
        )

        with engine.begin() as connection:
            poi_exists = connection.execute(
                poi_query,
                {"poi_id": poi_id},
            ).first()

            if poi_exists is None:
                return None

            for record in records:
                connection.execute(insert_query, record)

            rows = connection.execute(
                select_query,
                {"poi_id": poi_id},
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def replace_all_for_owner(
        self,
        records: list[dict],
        owner_id: int,
    ) -> list[dict] | None:
        """Cập nhật hoặc bổ sung đủ năm ngôn ngữ trong một transaction."""
        if not records:
            return []

        poi_id = records[0]["poi_id"]
        owner_query = text(
            """
            SELECT 1
            FROM dbo.pois
            WHERE id = :poi_id
              AND owner_id = :owner_id
            """
        )
        update_query = text(
            """
            UPDATE dbo.translations
            SET
                title = :title,
                narration_text = :narration_text,
                audio_url = :audio_url,
                is_machine_generated = :is_machine_generated,
                updated_at = SYSUTCDATETIME()
            WHERE poi_id = :poi_id
              AND language_code = :language_code
            """
        )
        insert_query = text(
            """
            INSERT INTO dbo.translations
            (
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_machine_generated,
                is_active
            )
            VALUES
            (
                :poi_id,
                :language_code,
                :title,
                :narration_text,
                :audio_url,
                :is_machine_generated,
                1
            )
            """
        )
        select_query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.poi_id = :poi_id
              AND poi.owner_id = :owner_id
            ORDER BY translation.language_code
            """
        )

        with engine.begin() as connection:
            owns_poi = connection.execute(
                owner_query,
                {"poi_id": poi_id, "owner_id": owner_id},
            ).first()

            if owns_poi is None:
                return None

            for record in records:
                result = connection.execute(update_query, record)
                if result.rowcount == 0:
                    connection.execute(insert_query, record)

            rows = connection.execute(
                select_query,
                {"poi_id": poi_id, "owner_id": owner_id},
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def replace_all_as_system_admin(
        self,
        records: list[dict],
    ) -> list[dict] | None:
        """SYSTEM_ADMIN cập nhật hoặc bổ sung năm ngôn ngữ của mọi POI."""
        if not records:
            return []

        poi_id = records[0]["poi_id"]
        poi_query = text(
            """
            SELECT 1
            FROM dbo.pois
            WHERE id = :poi_id
            """
        )
        update_query = text(
            """
            UPDATE dbo.translations
            SET
                title = :title,
                narration_text = :narration_text,
                audio_url = :audio_url,
                is_machine_generated = :is_machine_generated,
                updated_at = SYSUTCDATETIME()
            WHERE poi_id = :poi_id
              AND language_code = :language_code
            """
        )
        insert_query = text(
            """
            INSERT INTO dbo.translations
            (
                poi_id,
                language_code,
                title,
                narration_text,
                audio_url,
                is_machine_generated,
                is_active
            )
            VALUES
            (
                :poi_id,
                :language_code,
                :title,
                :narration_text,
                :audio_url,
                :is_machine_generated,
                1
            )
            """
        )
        select_query = text(
            f"""
            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.poi_id = :poi_id
            ORDER BY translation.language_code
            """
        )

        with engine.begin() as connection:
            poi_exists = connection.execute(
                poi_query,
                {"poi_id": poi_id},
            ).first()

            if poi_exists is None:
                return None

            for record in records:
                result = connection.execute(update_query, record)
                if result.rowcount == 0:
                    connection.execute(insert_query, record)

            rows = connection.execute(
                select_query,
                {"poi_id": poi_id},
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def update_audio_for_owner(
        self,
        translation_id: int,
        owner_id: int,
        audio_url: str,
    ) -> dict | None:
        """Đổi audio nếu bản dịch thuộc POI của SHOP_OWNER hiện tại."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE translation
            SET
                audio_url = :audio_url,
                updated_at = SYSUTCDATETIME()
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.id = :translation_id
              AND poi.owner_id = :owner_id;

            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.id = :translation_id
              AND poi.owner_id = :owner_id;
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "translation_id": translation_id,
                    "owner_id": owner_id,
                    "audio_url": audio_url,
                },
            ).mappings().first()

        return self._row_to_dict(row)

    def update_audio_as_system_admin(
        self,
        translation_id: int,
        audio_url: str,
    ) -> dict | None:
        """SYSTEM_ADMIN tạo lại audio của một bản dịch bất kỳ."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE dbo.translations
            SET
                audio_url = :audio_url,
                updated_at = SYSUTCDATETIME()
            WHERE id = :translation_id;

            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.id = :translation_id;
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "translation_id": translation_id,
                    "audio_url": audio_url,
                },
            ).mappings().first()

        return self._row_to_dict(row)

    def set_visibility_for_owner(
        self,
        translation_id: int,
        owner_id: int,
        is_active: bool,
    ) -> dict | None:
        """Ẩn/hiện bản dịch thuộc đúng chủ quán, không xóa dữ liệu/audio."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE translation
            SET
                is_active = :is_active,
                updated_at = SYSUTCDATETIME()
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.id = :translation_id
              AND poi.owner_id = :owner_id;

            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            INNER JOIN dbo.pois AS poi
                ON poi.id = translation.poi_id
            WHERE translation.id = :translation_id
              AND poi.owner_id = :owner_id;
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "translation_id": translation_id,
                    "owner_id": owner_id,
                    "is_active": is_active,
                },
            ).mappings().first()

        return self._row_to_dict(row)

    def set_visibility_as_system_admin(
        self,
        translation_id: int,
        is_active: bool,
    ) -> dict | None:
        """SYSTEM_ADMIN ẩn/hiện bản dịch bất kỳ nhưng không xóa dữ liệu."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE dbo.translations
            SET
                is_active = :is_active,
                updated_at = SYSUTCDATETIME()
            WHERE id = :translation_id;

            SELECT {self.SELECT_COLUMNS}
            FROM dbo.translations AS translation
            WHERE translation.id = :translation_id;
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "translation_id": translation_id,
                    "is_active": is_active,
                },
            ).mappings().first()

        return self._row_to_dict(row)


translation_repository = TranslationRepository()

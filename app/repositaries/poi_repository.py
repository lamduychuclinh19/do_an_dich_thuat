"""Repository SQL Server cho POI, có cô lập dữ liệu theo chủ địa điểm."""

from sqlalchemy import text

from app.database import engine


class PoiRepository:
    """Đọc và ghi bảng ``dbo.pois`` trong MuseumGuideDB_V2."""

    @staticmethod
    def _row_to_dict(row) -> dict | None:
        """Chuyển một dòng SQLAlchemy thành dict để trả cho service."""
        if row is None:
            return None

        poi = dict(row)
        poi["is_active"] = bool(poi["is_active"])
        return poi

    @staticmethod
    def _select_columns() -> str:
        """Danh sách cột dùng chung để các câu SELECT luôn đồng nhất."""
        return """
            id,
            owner_id,
            name,
            description,
            address,
            latitude,
            longitude,
            trigger_radius_meters,
            is_active,
            created_at,
            updated_at
        """

    def create(
        self,
        data: dict,
        owner_id: int,
        poi_id: str,
    ) -> dict:
        """Tạo POI với mã NVARCHAR do người quản lý nhập."""
        query = text(
            f"""
            SET NOCOUNT ON;

            INSERT INTO dbo.pois
            (
                id,
                owner_id,
                name,
                description,
                address,
                latitude,
                longitude,
                trigger_radius_meters,
                is_active
            )
            VALUES
            (
                :poi_id,
                :owner_id,
                :name,
                :description,
                :address,
                :latitude,
                :longitude,
                :trigger_radius_meters,
                1
            );

            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE id = :poi_id;
            """
        )

        parameters = {
            **data,
            "owner_id": owner_id,
            "poi_id": poi_id,
        }

        with engine.begin() as connection:
            row = connection.execute(
                query,
                parameters,
            ).mappings().one()

        return self._row_to_dict(row)

    def get_by_id(self, poi_id: str) -> dict | None:
        """Lấy POI theo ID; service public sẽ tự chặn POI đang ẩn."""
        query = text(
            f"""
            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE id = :poi_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"poi_id": poi_id},
            ).mappings().first()

        return self._row_to_dict(row)

    def get_by_id_for_owner(
        self,
        poi_id: str,
        owner_id: int,
    ) -> dict | None:
        """Chỉ tìm thấy POI khi POI thuộc đúng chủ quán đang đăng nhập."""
        query = text(
            f"""
            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE id = :poi_id
              AND owner_id = :owner_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {
                    "poi_id": poi_id,
                    "owner_id": owner_id,
                },
            ).mappings().first()

        return self._row_to_dict(row)

    def update(
        self,
        poi_id: str,
        owner_id: int,
        data: dict,
    ) -> dict | None:
        """Cập nhật POI nếu ID và owner_id cùng khớp."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE dbo.pois
            SET
                name = :name,
                description = :description,
                address = :address,
                latitude = :latitude,
                longitude = :longitude,
                trigger_radius_meters = :trigger_radius_meters,
                updated_at = SYSUTCDATETIME()
            WHERE id = :poi_id
              AND owner_id = :owner_id;

            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE id = :poi_id
              AND owner_id = :owner_id;
            """
        )

        parameters = {
            **data,
            "poi_id": poi_id,
            "owner_id": owner_id,
        }

        with engine.begin() as connection:
            row = connection.execute(
                query,
                parameters,
            ).mappings().first()

        return self._row_to_dict(row)

    def set_visibility(
        self,
        poi_id: str,
        owner_id: int,
        is_active: bool,
    ) -> dict | None:
        """Ẩn/hiện POI thuộc đúng chủ quán; không xóa dữ liệu."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE dbo.pois
            SET
                is_active = :is_active,
                updated_at = SYSUTCDATETIME()
            WHERE id = :poi_id
              AND owner_id = :owner_id;

            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE id = :poi_id
              AND owner_id = :owner_id;
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "poi_id": poi_id,
                    "owner_id": owner_id,
                    "is_active": is_active,
                },
            ).mappings().first()

        return self._row_to_dict(row)

    def get_active(self) -> list[dict]:
        """Danh sách public: chỉ trả các POI đang hoạt động."""
        query = text(
            f"""
            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE is_active = 1
            ORDER BY created_at DESC, id DESC
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(query).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def get_all_for_owner(self, owner_id: int) -> list[dict]:
        """SHOP_OWNER thấy cả POI đang hiện và đang ẩn của chính mình."""
        query = text(
            f"""
            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE owner_id = :owner_id
            ORDER BY created_at DESC, id DESC
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                {"owner_id": owner_id},
            ).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def get_all_for_system_admin(self) -> list[dict]:
        """SYSTEM_ADMIN thấy toàn bộ POI của mọi SHOP_OWNER.

        Hàm này không lọc ``owner_id`` vì quản trị hệ thống có trách nhiệm
        hỗ trợ và quản lý nội dung trên toàn hệ thống.
        """
        query = text(
            f"""
            SELECT {self._select_columns()}
            FROM dbo.pois
            ORDER BY created_at DESC, id DESC
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(query).mappings().all()

        return [self._row_to_dict(row) for row in rows]

    def update_as_system_admin(
        self,
        poi_id: str,
        data: dict,
    ) -> dict | None:
        """SYSTEM_ADMIN cập nhật POI bất kỳ, không lọc theo owner_id."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE dbo.pois
            SET
                name = :name,
                description = :description,
                address = :address,
                latitude = :latitude,
                longitude = :longitude,
                trigger_radius_meters = :trigger_radius_meters,
                updated_at = SYSUTCDATETIME()
            WHERE id = :poi_id;

            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE id = :poi_id;
            """
        )

        parameters = {
            **data,
            "poi_id": poi_id,
        }

        with engine.begin() as connection:
            row = connection.execute(
                query,
                parameters,
            ).mappings().first()

        return self._row_to_dict(row)

    def set_visibility_as_system_admin(
        self,
        poi_id: str,
        is_active: bool,
    ) -> dict | None:
        """SYSTEM_ADMIN ẩn/hiện POI bất kỳ, không xóa dữ liệu."""
        query = text(
            f"""
            SET NOCOUNT ON;

            UPDATE dbo.pois
            SET
                is_active = :is_active,
                updated_at = SYSUTCDATETIME()
            WHERE id = :poi_id;

            SELECT {self._select_columns()}
            FROM dbo.pois
            WHERE id = :poi_id;
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "poi_id": poi_id,
                    "is_active": is_active,
                },
            ).mappings().first()

        return self._row_to_dict(row)


poi_repository = PoiRepository()

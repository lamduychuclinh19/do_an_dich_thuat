from sqlalchemy import text

from app.database import engine


class PoiRepository:
    def _convert_row_to_dict(self, row) -> dict | None:
        if row is None:
            return None

        poi = dict(row)

        # SQL Server trả DECIMAL, trong khi Service tính khoảng cách bằng float.
        poi["latitude"] = float(poi["latitude"])
        poi["longitude"] = float(poi["longitude"])
        poi["trigger_radius_meters"] = float(
            poi["trigger_radius_meters"]
        )
        poi["is_active"] = bool(poi["is_active"])

        return poi

    def create(self, data: dict) -> dict:
        query = text(
            """
            INSERT INTO dbo.pois
            (
                name,
                description,
                address,
                latitude,
                longitude,
                trigger_radius_meters,
                is_active
            )
            OUTPUT
                INSERTED.id,
                INSERTED.name,
                INSERTED.description,
                INSERTED.address,
                INSERTED.latitude,
                INSERTED.longitude,
                INSERTED.trigger_radius_meters,
                INSERTED.is_active
            VALUES
            (
                :name,
                :description,
                :address,
                :latitude,
                :longitude,
                :trigger_radius_meters,
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

    def get_by_id(self, poi_id: int) -> dict | None:
        query = text(
            """
            SELECT
                id,
                name,
                description,
                address,
                latitude,
                longitude,
                trigger_radius_meters,
                is_active
            FROM dbo.pois
            WHERE id = :poi_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"poi_id": poi_id},
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def update(self, poi_id: int, data: dict) -> dict | None:
        query = text(
            """
            UPDATE dbo.pois
            SET
                name = :name,
                description = :description,
                address = :address,
                latitude = :latitude,
                longitude = :longitude,
                trigger_radius_meters = :trigger_radius_meters,
                updated_at = SYSUTCDATETIME()
            OUTPUT
                INSERTED.id,
                INSERTED.name,
                INSERTED.description,
                INSERTED.address,
                INSERTED.latitude,
                INSERTED.longitude,
                INSERTED.trigger_radius_meters,
                INSERTED.is_active
            WHERE id = :poi_id
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

        return self._convert_row_to_dict(row)

    def set_visibility(
        self,
        poi_id: int,
        is_active: bool,
    ) -> dict | None:
        query = text(
            """
            UPDATE dbo.pois
            SET
                is_active = :is_active,
                updated_at = SYSUTCDATETIME()
            OUTPUT
                INSERTED.id,
                INSERTED.name,
                INSERTED.description,
                INSERTED.address,
                INSERTED.latitude,
                INSERTED.longitude,
                INSERTED.trigger_radius_meters,
                INSERTED.is_active
            WHERE id = :poi_id
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

        return self._convert_row_to_dict(row)

    def get_active(self) -> list[dict]:
        query = text(
            """
            SELECT
                id,
                name,
                description,
                address,
                latitude,
                longitude,
                trigger_radius_meters,
                is_active
            FROM dbo.pois
            WHERE is_active = 1
            ORDER BY id
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(query).mappings().all()

        return [
            self._convert_row_to_dict(row)
            for row in rows
        ]

    def get_all(self) -> list[dict]:
        query = text(
            """
            SELECT
                id,
                name,
                description,
                address,
                latitude,
                longitude,
                trigger_radius_meters,
                is_active
            FROM dbo.pois
            ORDER BY id
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(query).mappings().all()

        return [
            self._convert_row_to_dict(row)
            for row in rows
        ]


poi_repository = PoiRepository()
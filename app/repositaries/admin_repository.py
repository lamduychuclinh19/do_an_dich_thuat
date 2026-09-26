from sqlalchemy import text

from app.database import engine


class AdminRepository:
    def _convert_row_to_dict(self, row) -> dict | None:
        if row is None:
            return None

        admin = dict(row)
        admin["is_active"] = bool(admin["is_active"])

        return admin

    def get_by_username(
        self,
        username: str,
    ) -> dict | None:
        query = text(
            """
            SELECT
                id,
                username,
                password_hash,
                is_active
            FROM dbo.admins
            WHERE username = :username
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"username": username},
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def get_by_id(
        self,
        admin_id: int,
    ) -> dict | None:
        query = text(
            """
            SELECT
                id,
                username,
                password_hash,
                is_active
            FROM dbo.admins
            WHERE id = :admin_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"admin_id": admin_id},
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def create(self,username: str,password_hash: str,) -> dict:
        query = text(
            """
            INSERT INTO dbo.admins
            (
                username,
                password_hash,
                is_active
            )
            OUTPUT
                INSERTED.id,
                INSERTED.username,
                INSERTED.password_hash,
                INSERTED.is_active
            VALUES
            (
                :username,
                :password_hash,
                1
            )
            """
        )

        with engine.begin() as connection:
            row = connection.execute(
                query,
                {
                    "username": username,
                    "password_hash": password_hash,
                },
            ).mappings().one()

        return self._convert_row_to_dict(row)


admin_repository = AdminRepository()
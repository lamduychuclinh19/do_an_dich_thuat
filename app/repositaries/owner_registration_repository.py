"""SQL Server persistence for SHOP_OWNER registration requests."""

from sqlalchemy import text

from app.database import engine


class OwnerRegistrationRepository:
    """Truy vấn phiếu đăng ký chủ quán và hoàn tất quyết định admin."""
    def create(self, data: dict) -> dict:
        """Lưu một phiếu đăng ký mới ở trạng thái chờ xét duyệt."""
        query = text("""
            INSERT INTO dbo.poi_owner_registrations
                (username, password_hash, full_name, phone, email)
            OUTPUT INSERTED.id, INSERTED.username, INSERTED.full_name,
                   INSERTED.phone, INSERTED.email, INSERTED.created_at,
                   INSERTED.reviewed_at, INSERTED.status, INSERTED.admin_note
            VALUES (:username, :password_hash, :full_name, :phone, :email)
        """)
        with engine.begin() as connection:
            row = connection.execute(query, data).mappings().one()
        return dict(row)

    def list_all(self) -> list[dict]:
        """Đọc danh sách phiếu đăng ký cùng thông tin xử lý."""
        query = text("""
            SELECT id, username, full_name, phone, email, created_at,
                   reviewed_at, status, admin_note
            FROM dbo.poi_owner_registrations
            ORDER BY CASE WHEN status IS NULL THEN 0 ELSE 1 END,
                     created_at DESC,
                     id DESC
        """)
        with engine.connect() as connection:
            return [dict(row) for row in connection.execute(query).mappings()]

    def count_pending(self) -> int:
        """Đếm số phiếu đăng ký chưa được admin xử lý."""
        query = text("""
            SELECT COUNT(*)
            FROM dbo.poi_owner_registrations
            WHERE reviewed_at IS NULL
        """)
        with engine.connect() as connection:
            return int(connection.execute(query).scalar_one())

    def get_by_id(self, registration_id: int) -> dict | None:
        """Lấy một phiếu đăng ký theo mã phiếu."""
        query = text("""
            SELECT id, username, password_hash, full_name, phone, email,
                   created_at, reviewed_at, status, admin_note
            FROM dbo.poi_owner_registrations WHERE id = :id
        """)
        with engine.connect() as connection:
            row = connection.execute(query, {"id": registration_id}).mappings().first()
        return dict(row) if row else None

    def decide(self, registration: dict, admin: dict, decision: int, note: str) -> bool:
        """Atomically create the account on approval and finalize the request."""
        with engine.begin() as connection:
            current = connection.execute(text("""
                SELECT id, username, password_hash, full_name, phone, email
                FROM dbo.poi_owner_registrations WITH (UPDLOCK, ROWLOCK)
                WHERE id = :id AND reviewed_at IS NULL
            """), {"id": registration["id"]}).mappings().first()
            if current is None:
                return False
            if decision == 1:
                connection.execute(text("""
                    INSERT INTO dbo.people
                        (username, password_hash, full_name, phone, email,
                         role, is_active, must_change_password, created_by_person_id)
                    VALUES
                        (:username, :password_hash, :full_name, :phone, :email,
                         'SHOP_OWNER', 1, 0, :admin_id)
                """), {**dict(current), "admin_id": admin["id"]})
            connection.execute(text("""
                UPDATE dbo.poi_owner_registrations
                SET status = :status, admin_note = :note,
                    reviewed_at = SYSUTCDATETIME(), reviewed_by_username = :admin_username
                WHERE id = :id
            """), {"status": decision, "note": note, "admin_username": admin["username"], "id": registration["id"]})
        return True


owner_registration_repository = OwnerRegistrationRepository()

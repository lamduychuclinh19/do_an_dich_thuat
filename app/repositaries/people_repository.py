"""Repository truy cập bảng dbo.people trong MuseumGuideDB_V2.

Một bảng ``people`` dùng chung cho ba nhóm tài khoản:
- SYSTEM_ADMIN: quản trị toàn hệ thống.
- SHOP_OWNER: chủ địa điểm, quản lý nội dung thuyết minh.
- TOURIST: khách du lịch sử dụng nội dung sau khi thanh toán.
"""

from sqlalchemy import text

from app.database import engine


class PeopleRepository:
    """Thực hiện các câu lệnh SQL liên quan đến tài khoản người dùng."""

    @staticmethod
    def _row_to_dict(row):
        """Chuyển SQLAlchemy Row thành dict và chuẩn hóa kiểu BIT."""
        if row is None:
            return None

        person = dict(row._mapping)

        if "is_active" in person:
            person["is_active"] = bool(person["is_active"])

        if "must_change_password" in person:
            person["must_change_password"] = bool(
                person["must_change_password"]
            )

        # Tên tương thích tạm thời với schema/router cũ. Khi toàn bộ backend
        # chuyển sang V2, ta sẽ dùng created_by_person_id hoàn toàn.
        if "created_by_person_id" in person:
            person["created_by_admin_id"] = person[
                "created_by_person_id"
            ]

        return person

    def get_by_username(self, username: str):
        """Tìm tài khoản theo username để phục vụ đăng nhập.

        Đăng nhập không cần tên quán nên câu query này chỉ đọc bảng people.
        Tên quán sẽ được lấy từ pois.name ở chức năng quản lý SHOP_OWNER.
        """
        query = text(
            """
            SELECT
                p.id,
                p.username,
                p.password_hash,
                p.full_name,
                p.phone,
                p.email,
                p.role,
                p.is_active,
                p.must_change_password,
                p.last_login_at,
                p.created_by_person_id,
                p.created_at,
                p.updated_at
            FROM dbo.people AS p
            WHERE p.username = :username
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"username": username},
            ).fetchone()

        return self._row_to_dict(row)

    def get_by_id(self, person_id: int):
        """Tìm tài khoản theo khóa chính và lấy tên địa điểm từ pois."""
        query = text(
            """
            SELECT
                p.id,
                p.username,
                p.password_hash,
                p.full_name,
                shops.shop_name,
                p.phone,
                p.email,
                p.role,
                p.is_active,
                p.must_change_password,
                p.last_login_at,
                p.created_by_person_id,
                p.created_at,
                p.updated_at
            FROM dbo.people AS p
            OUTER APPLY (
                SELECT STRING_AGG(
                    CAST(poi.name AS NVARCHAR(MAX)),
                    N', '
                ) AS shop_name
                FROM dbo.pois AS poi
                WHERE poi.owner_id = p.id
            ) AS shops
            WHERE p.id = :person_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"person_id": person_id},
            ).fetchone()

        return self._row_to_dict(row)

    def get_by_phone(self, phone: str):
        """Kiểm tra số điện thoại đã được tài khoản nào sử dụng chưa."""
        query = text(
            """
            SELECT id, username, phone, role
            FROM dbo.people
            WHERE phone = :phone
            """
        )

        with engine.connect() as connection:
            row = connection.execute(query, {"phone": phone}).fetchone()

        return self._row_to_dict(row)

    def get_by_email(self, email: str):
        """Kiểm tra email đã được tài khoản nào sử dụng chưa."""
        query = text(
            """
            SELECT id, username, email, role
            FROM dbo.people
            WHERE email = :email
            """
        )

        with engine.connect() as connection:
            row = connection.execute(query, {"email": email}).fetchone()

        return self._row_to_dict(row)

    def get_all_shop_owners(
        self,
        phone_keyword: str | None = None,
        is_active: bool | None = None,
        keyword: str | None = None,
    ):
        """Lấy SHOP_OWNER, tìm theo tên quán/SĐT và lọc trạng thái."""
        conditions = ["p.role = 'SHOP_OWNER'"]
        parameters = {}

        # phone_keyword được giữ để router/service cũ chưa bị lỗi trong lúc
        # chuyển đổi. API mới sẽ gửi một keyword dùng chung cho cả hai cột.
        search_keyword = keyword or phone_keyword
        if search_keyword:
            conditions.append(
                """(
                    p.phone LIKE :keyword
                    OR EXISTS (
                        SELECT 1
                        FROM dbo.pois AS searched_poi
                        WHERE searched_poi.owner_id = p.id
                          AND searched_poi.name LIKE :keyword
                    )
                )"""
            )
            parameters["keyword"] = f"%{search_keyword.strip()}%"

        if is_active is not None:
            conditions.append("p.is_active = :is_active")
            parameters["is_active"] = int(is_active)

        where_clause = " AND ".join(conditions)
        query = text(
            f"""
            SELECT
                p.id,
                p.username,
                p.full_name,
                shops.shop_name,
                p.phone,
                p.email,
                p.role,
                p.is_active,
                p.must_change_password,
                p.last_login_at,
                p.created_by_person_id,
                p.created_at,
                p.updated_at
            FROM dbo.people AS p
            OUTER APPLY (
                SELECT STRING_AGG(
                    CAST(poi.name AS NVARCHAR(MAX)),
                    N', '
                ) AS shop_name
                FROM dbo.pois AS poi
                WHERE poi.owner_id = p.id
            ) AS shops
            WHERE {where_clause}
            ORDER BY p.created_at DESC, p.id DESC
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def create_shop_owner(
        self,
        data,
        password_hash: str,
        created_by_system_admin_id: int,
    ):
        """Tạo SHOP_OWNER; mật khẩu mặc định đã được băm ở service."""
        query = text(
            """
            INSERT INTO dbo.people (
                username,
                password_hash,
                full_name,
                phone,
                email,
                role,
                is_active,
                must_change_password,
                created_by_person_id
            )
            VALUES (
                :username,
                :password_hash,
                :full_name,
                :phone,
                :email,
                'SHOP_OWNER',
                1,
                1,
                :created_by_person_id
            )
            """
        )

        parameters = {
            "username": data.username.strip(),
            "password_hash": password_hash,
            "full_name": data.full_name.strip(),
            "phone": data.phone.strip() if data.phone else None,
            "email": data.email.strip().lower(),
            "created_by_person_id": created_by_system_admin_id,
        }

        # dbo.people có trigger nên SQL Server không cho dùng OUTPUT trực
        # tiếp. Ta INSERT trước rồi SELECT lại trong cùng transaction.
        with engine.begin() as connection:
            connection.execute(query, parameters)
            row = connection.execute(
                text(
                    """
                    SELECT
                        p.id,
                        p.username,
                        p.full_name,
                        shops.shop_name,
                        p.phone,
                        p.email,
                        p.role,
                        p.is_active,
                        p.must_change_password,
                        p.last_login_at,
                        p.created_by_person_id,
                        p.created_at,
                        p.updated_at
                    FROM dbo.people AS p
                    OUTER APPLY (
                        SELECT STRING_AGG(
                            CAST(poi.name AS NVARCHAR(MAX)),
                            N', '
                        ) AS shop_name
                        FROM dbo.pois AS poi
                        WHERE poi.owner_id = p.id
                    ) AS shops
                    WHERE p.username = :username
                    """
                ),
                {"username": parameters["username"]},
            ).fetchone()

        return self._row_to_dict(row)

    def update_shop_owner(self, person_id: int, data):
        """Sửa thông tin và trạng thái SHOP_OWNER, không đổi vai trò."""
        query = text(
            """
            UPDATE dbo.people
            SET
                full_name = :full_name,
                phone = :phone,
                email = :email,
                is_active = :is_active,
                updated_at = SYSUTCDATETIME()
            WHERE id = :person_id
              AND role = 'SHOP_OWNER'
            """
        )

        parameters = {
            "person_id": person_id,
            "full_name": data.full_name.strip(),
            "phone": data.phone.strip() if data.phone else None,
            "email": data.email.strip().lower(),
            "is_active": int(data.is_active),
        }

        # UPDATE trước rồi đọc lại, tránh OUTPUT trên bảng có trigger.
        with engine.begin() as connection:
            connection.execute(query, parameters)
            row = connection.execute(
                text(
                    """
                    SELECT
                        p.id,
                        p.username,
                        p.full_name,
                        shops.shop_name,
                        p.phone,
                        p.email,
                        p.role,
                        p.is_active,
                        p.must_change_password,
                        p.last_login_at,
                        p.created_by_person_id,
                        p.created_at,
                        p.updated_at
                    FROM dbo.people AS p
                    OUTER APPLY (
                        SELECT STRING_AGG(
                            CAST(poi.name AS NVARCHAR(MAX)),
                            N', '
                        ) AS shop_name
                        FROM dbo.pois AS poi
                        WHERE poi.owner_id = p.id
                    ) AS shops
                    WHERE p.id = :person_id
                      AND p.role = 'SHOP_OWNER'
                    """
                ),
                {"person_id": person_id},
            ).fetchone()

        return self._row_to_dict(row)

    def reset_shop_owner_password(
        self,
        person_id: int,
        password_hash: str,
    ) -> bool:
        """Đặt lại mật khẩu và buộc chủ địa điểm đổi ở lần đăng nhập sau."""
        query = text(
            """
            UPDATE dbo.people
            SET
                password_hash = :password_hash,
                must_change_password = 1,
                updated_at = SYSUTCDATETIME()
            WHERE id = :person_id
              AND role = 'SHOP_OWNER'
            """
        )

        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "person_id": person_id,
                    "password_hash": password_hash,
                },
            )

        return result.rowcount > 0

    def update_own_profile(self, person_id: int, data):
        """SHOP_OWNER tự sửa thông tin của mình, không được đổi role/status.

        ``person_id`` luôn lấy từ JWT ở backend. Client không được gửi ID
        tài khoản cần sửa nên không thể sửa hồ sơ của người khác.
        """
        update_query = text(
            """
            UPDATE dbo.people
            SET
                full_name = :full_name,
                phone = :phone,
                email = :email,
                updated_at = SYSUTCDATETIME()
            WHERE id = :person_id
              AND role = 'SHOP_OWNER'
            """
        )

        select_query = text(
            """
            SELECT
                p.id,
                p.username,
                p.full_name,
                shops.shop_name,
                p.phone,
                p.email,
                p.role,
                p.is_active,
                p.must_change_password,
                p.last_login_at,
                p.created_by_person_id,
                p.created_at,
                p.updated_at
            FROM dbo.people AS p
            OUTER APPLY (
                SELECT STRING_AGG(
                    CAST(poi.name AS NVARCHAR(MAX)),
                    N', '
                ) AS shop_name
                FROM dbo.pois AS poi
                WHERE poi.owner_id = p.id
            ) AS shops
            WHERE p.id = :person_id
              AND p.role = 'SHOP_OWNER'
            """
        )

        parameters = {
            "person_id": person_id,
            "full_name": data.full_name.strip(),
            "phone": data.phone.strip() if data.phone else None,
            "email": data.email.strip().lower(),
        }

        with engine.begin() as connection:
            connection.execute(update_query, parameters)
            row = connection.execute(
                select_query,
                {"person_id": person_id},
            ).fetchone()

        return self._row_to_dict(row)

    def update_own_password(
        self,
        person_id: int,
        password_hash: str,
    ) -> bool:
        """Lưu hash mới và bỏ cờ buộc đổi mật khẩu mặc định."""
        query = text(
            """
            UPDATE dbo.people
            SET
                password_hash = :password_hash,
                must_change_password = 0,
                updated_at = SYSUTCDATETIME()
            WHERE id = :person_id
              AND role = 'SHOP_OWNER'
              AND is_active = 1
            """
        )

        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "person_id": person_id,
                    "password_hash": password_hash,
                },
            )

        return result.rowcount > 0

    def create_tourist(self, data, password_hash: str):
        """Tạo tài khoản khách du lịch tự đăng ký."""
        query = text(
            """
            INSERT INTO dbo.people (
                username,
                password_hash,
                full_name,
                phone,
                email,
                role,
                is_active,
                must_change_password,
                created_by_person_id
            )
            VALUES (
                :username,
                :password_hash,
                :full_name,
                :phone,
                :email,
                'TOURIST',
                1,
                0,
                NULL
            )
            """
        )

        parameters = {
            "username": data.username.strip(),
            "password_hash": password_hash,
            "full_name": data.full_name.strip(),
            "phone": data.phone.strip() if data.phone else None,
            "email": data.email.strip().lower(),
        }

        # INSERT trước rồi SELECT lại vì dbo.people đang bật trigger.
        with engine.begin() as connection:
            connection.execute(query, parameters)
            row = connection.execute(
                text(
                    """
                    SELECT
                        id,
                        username,
                        full_name,
                        phone,
                        email,
                        role,
                        is_active,
                        must_change_password,
                        last_login_at,
                        created_by_person_id,
                        created_at,
                        updated_at
                    FROM dbo.people
                    WHERE username = :username
                    """
                ),
                {"username": parameters["username"]},
            ).fetchone()

        return self._row_to_dict(row)

    def update_last_login(self, person_id: int) -> None:
        """Lưu thời điểm đăng nhập thành công gần nhất."""
        query = text(
            """
            UPDATE dbo.people
            SET
                last_login_at = SYSUTCDATETIME(),
                updated_at = SYSUTCDATETIME()
            WHERE id = :person_id
            """
        )

        with engine.begin() as connection:
            connection.execute(query, {"person_id": person_id})

    def has_active_tourist_access(self, person_id: int) -> bool:
        """Kiểm tra TOURIST còn thời hạn sử dụng từ giao dịch thành công."""
        query = text(
            """
            SELECT TOP 1 1
            FROM dbo.vw_active_tourist_access
            WHERE person_id = :person_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {"person_id": person_id},
            ).fetchone()

        return row is not None

    # Các tên dưới đây giữ backend hiện tại hoạt động trong lúc đổi dần từ
    # "admin" sang "people". Sau khi sửa hết service/router có thể xóa chúng.
    def get_all(self, phone_keyword=None, is_active=None):
        return self.get_all_shop_owners(phone_keyword, is_active)

    def create_staff(self, data, password_hash, created_by_admin_id):
        return self.create_shop_owner(
            data,
            password_hash,
            created_by_admin_id,
        )

    def update_staff(self, admin_id, data):
        return self.update_shop_owner(admin_id, data)

    def reset_staff_password(self, admin_id, password_hash):
        return self.reset_shop_owner_password(admin_id, password_hash)


people_repository = PeopleRepository()

# Alias tạm thời để việc đổi import ở các file khác diễn ra từng bước.
admin_repository = people_repository

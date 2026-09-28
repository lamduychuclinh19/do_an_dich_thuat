from sqlalchemy import text

from app.database import engine


class AdminRepository:
    def _convert_row_to_dict(
        self,
        row,
    ) -> dict | None:
        """
        Chuyển kết quả SQLAlchemy thành dictionary.

        SQL Server trả BIT dưới dạng 0/1 nên cần chuyển
        thành bool để FastAPI trả true/false đúng chuẩn JSON.
        """
        if row is None:
            return None

        admin = dict(row)

        if "is_active" in admin:
            admin["is_active"] = bool(
                admin["is_active"]
            )

        if "must_change_password" in admin:
            admin["must_change_password"] = bool(
                admin["must_change_password"]
            )

        return admin

    def get_by_username(
        self,
        username: str,
    ) -> dict | None:
        """
        Tìm tài khoản bằng username.

        Hàm này được phần đăng nhập sử dụng nên cần lấy
        password_hash, role và trạng thái tài khoản.
        """
        query = text(
            """
            SELECT
                id,
                username,
                password_hash,
                full_name,
                phone,
                email,
                role,
                is_active,
                must_change_password,
                last_login_at,
                created_by_admin_id,
                created_at
            FROM dbo.admins
            WHERE username = :username
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {
                    "username": username,
                },
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def get_by_id(
        self,
        admin_id: int,
    ) -> dict | None:
        """
        Lấy tài khoản theo mã quản trị viên.

        Auth dependency sẽ dùng hàm này để kiểm tra lại
        role và is_active trực tiếp từ database.
        """
        query = text(
            """
            SELECT
                id,
                username,
                password_hash,
                full_name,
                phone,
                email,
                role,
                is_active,
                must_change_password,
                last_login_at,
                created_by_admin_id,
                created_at
            FROM dbo.admins
            WHERE id = :admin_id
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {
                    "admin_id": admin_id,
                },
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def get_by_phone(
        self,
        phone: str,
    ) -> dict | None:
        """Kiểm tra số điện thoại đã được sử dụng chưa."""
        query = text(
            """
            SELECT
                id,
                username,
                phone
            FROM dbo.admins
            WHERE phone = :phone
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {
                    "phone": phone,
                },
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def get_by_email(
        self,
        email: str,
    ) -> dict | None:
        """Kiểm tra email đã được sử dụng chưa."""
        query = text(
            """
            SELECT
                id,
                username,
                email
            FROM dbo.admins
            WHERE email = :email
            """
        )

        with engine.connect() as connection:
            row = connection.execute(
                query,
                {
                    "email": email,
                },
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def get_all(
        self,
        phone_keyword: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict]:
        """
        Lấy danh sách quản trị viên.

        phone_keyword:
            Tìm kiếm gần đúng theo số điện thoại.

        is_active:
            None  -> lấy tất cả.
            True  -> chỉ tài khoản hoạt động.
            False -> chỉ tài khoản đã khóa.
        """
        conditions = []
        parameters = {}

        if phone_keyword:
            conditions.append(
                "phone LIKE :phone_keyword"
            )
            parameters["phone_keyword"] = (
                f"%{phone_keyword}%"
            )

        if is_active is not None:
            conditions.append(
                "is_active = :is_active"
            )
            parameters["is_active"] = is_active

        where_clause = ""

        if conditions:
            where_clause = (
                "WHERE " + " AND ".join(conditions)
            )

        query = text(
            f"""
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
                created_by_admin_id,
                created_at
            FROM dbo.admins
            {where_clause}
            ORDER BY
                CASE
                    WHEN role = 'OWNER' THEN 0
                    ELSE 1
                END,
                id
            """
        )

        with engine.connect() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).mappings().all()

        return [
            self._convert_row_to_dict(row)
            for row in rows
        ]

    def create_staff(
        self,
        data: dict,
        password_hash: str,
        created_by_admin_id: int,
    ) -> dict:
        """
        Tạo tài khoản nhân viên mới.

        Role luôn được backend đặt là STAFF.
        Không lấy role từ dữ liệu frontend gửi lên.
        """
        query = text(
            """
            INSERT INTO dbo.admins
            (
                username,
                password_hash,
                full_name,
                phone,
                email,
                role,
                is_active,
                must_change_password,
                created_by_admin_id
            )
            OUTPUT
                INSERTED.id,
                INSERTED.username,
                INSERTED.full_name,
                INSERTED.phone,
                INSERTED.email,
                INSERTED.role,
                INSERTED.is_active,
                INSERTED.must_change_password,
                INSERTED.last_login_at,
                INSERTED.created_by_admin_id,
                INSERTED.created_at
            VALUES
            (
                :username,
                :password_hash,
                :full_name,
                :phone,
                :email,
                'STAFF',
                1,
                1,
                :created_by_admin_id
            )
            """
        )

        parameters = {
            **data,
            "password_hash": password_hash,
            "created_by_admin_id": (
                created_by_admin_id
            ),
        }

        with engine.begin() as connection:
            row = connection.execute(
                query,
                parameters,
            ).mappings().one()

        return self._convert_row_to_dict(row)

    def update_staff(
        self,
        admin_id: int,
        data: dict,
    ) -> dict | None:
        """
        Sửa thông tin nhân viên.

        is_active nằm trong data của chức năng sửa,
        không có repository bật/tắt trạng thái riêng.

        WHERE role = 'STAFF' giúp bảo vệ tài khoản OWNER,
        kể cả khi service vô tình truyền ID của chủ quán.
        """
        allowed_fields = {
            "full_name",
            "phone",
            "email",
            "is_active",
        }

        update_data = {
            field: value
            for field, value in data.items()
            if field in allowed_fields
        }

        if not update_data:
            return self.get_by_id(admin_id)

        set_statements = [
            f"{field} = :{field}"
            for field in update_data
        ]

        query = text(
            f"""
            UPDATE dbo.admins
            SET {", ".join(set_statements)}
            OUTPUT
                INSERTED.id,
                INSERTED.username,
                INSERTED.full_name,
                INSERTED.phone,
                INSERTED.email,
                INSERTED.role,
                INSERTED.is_active,
                INSERTED.must_change_password,
                INSERTED.last_login_at,
                INSERTED.created_by_admin_id,
                INSERTED.created_at
            WHERE id = :admin_id
              AND role = 'STAFF'
            """
        )

        parameters = {
            **update_data,
            "admin_id": admin_id,
        }

        with engine.begin() as connection:
            row = connection.execute(
                query,
                parameters,
            ).mappings().first()

        return self._convert_row_to_dict(row)

    def reset_staff_password(
        self,
        admin_id: int,
        password_hash: str,
    ) -> bool:
        """
        Đặt lại mật khẩu nhân viên.

        Chỉ cập nhật STAFF, không cho API quản lý nhân sự
        đặt lại mật khẩu của OWNER.
        """
        query = text(
            """
            UPDATE dbo.admins
            SET
                password_hash = :password_hash,
                must_change_password = 1
            WHERE id = :admin_id
              AND role = 'STAFF'
            """
        )

        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "admin_id": admin_id,
                    "password_hash": password_hash,
                },
            )

        return result.rowcount > 0

    def update_last_login(
        self,
        admin_id: int,
    ) -> None:
        """
        Ghi nhận thời điểm tài khoản đăng nhập thành công.
        """
        query = text(
            """
            UPDATE dbo.admins
            SET last_login_at = SYSUTCDATETIME()
            WHERE id = :admin_id
            """
        )

        with engine.begin() as connection:
            connection.execute(
                query,
                {
                    "admin_id": admin_id,
                },
            )

    def create(
        self,
        username: str,
        password_hash: str,
    ) -> dict:
        """
        Giữ lại hàm cũ để không làm hỏng code đã sử dụng nó.

        Các tài khoản nhân viên mới phải được tạo bằng
        create_staff(), không dùng hàm này.
        """
        query = text(
            """
            INSERT INTO dbo.admins
            (
                username,
                password_hash,
                role,
                is_active,
                must_change_password
            )
            OUTPUT
                INSERTED.id,
                INSERTED.username,
                INSERTED.password_hash,
                INSERTED.role,
                INSERTED.is_active,
                INSERTED.must_change_password
            VALUES
            (
                :username,
                :password_hash,
                'STAFF',
                1,
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

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

    def get_all_shop_owners(
        self,
        phone_keyword: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict]:
        """
        Lấy danh sách tài khoản chủ quán.

        Màn hình quản lý tài khoản chỉ quản lý SHOP_OWNER,
        vì vậy SYSTEM_ADMIN không bao giờ xuất hiện trong kết quả.

        phone_keyword:
            Tìm kiếm gần đúng theo số điện thoại.

        is_active:
            None  -> lấy tất cả.
            True  -> chỉ tài khoản hoạt động.
            False -> chỉ tài khoản đã khóa.
        """
        conditions = ["role = 'SHOP_OWNER'"]
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
            ORDER BY id DESC
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

    def create_shop_owner(
        self,
        data: dict,
        password_hash: str,
        created_by_system_admin_id: int,
    ) -> dict:
        """
        Tạo tài khoản chủ quán mới.

        Role luôn do backend đặt là SHOP_OWNER, không lấy role
        từ frontend để tránh người dùng tự nâng quyền.
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
                'SHOP_OWNER',
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
                created_by_system_admin_id
            ),
        }

        with engine.begin() as connection:
            row = connection.execute(
                query,
                parameters,
            ).mappings().one()

        return self._convert_row_to_dict(row)

    def update_shop_owner(
        self,
        admin_id: int,
        data: dict,
    ) -> dict | None:
        """
        Sửa thông tin chủ quán.

        is_active nằm trong data của chức năng sửa,
        không có repository bật/tắt trạng thái riêng.

        Điều kiện role = SHOP_OWNER bảo vệ tài khoản
        SYSTEM_ADMIN ngay cả khi service truyền nhầm ID.
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
              AND role = 'SHOP_OWNER'
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

    def reset_shop_owner_password(
        self,
        admin_id: int,
        password_hash: str,
    ) -> bool:
        """
        Đặt lại mật khẩu chủ quán về mật khẩu mặc định.

        Chỉ cập nhật SHOP_OWNER, không cho API quản lý tài khoản
        đặt lại mật khẩu của SYSTEM_ADMIN.
        """
        query = text(
            """
            UPDATE dbo.admins
            SET
                password_hash = :password_hash,
                must_change_password = 1
            WHERE id = :admin_id
              AND role = 'SHOP_OWNER'
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

        Tài khoản chủ quán đầy đủ phải được tạo bằng
        create_shop_owner(), không dùng hàm này cho code mới.
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
                'SHOP_OWNER',
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

    def get_all(
        self,
        phone_keyword: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict]:
        return self.get_all_shop_owners(
            phone_keyword=phone_keyword,
            is_active=is_active,
        )

    def create_staff(
        self,
        data: dict,
        password_hash: str,
        created_by_admin_id: int,
    ) -> dict:
        return self.create_shop_owner(
            data=data,
            password_hash=password_hash,
            created_by_system_admin_id=(
                created_by_admin_id
            ),
        )

    def update_staff(
        self,
        admin_id: int,
        data: dict,
    ) -> dict | None:
        return self.update_shop_owner(
            admin_id=admin_id,
            data=data,
        )

    def reset_staff_password(
        self,
        admin_id: int,
        password_hash: str,
    ) -> bool:
        return self.reset_shop_owner_password(
            admin_id=admin_id,
            password_hash=password_hash,
        )


admin_repository = AdminRepository()

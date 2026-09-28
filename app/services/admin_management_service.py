from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from app.repositaries.admin_repository import (
    admin_repository,
)
from app.schemas.admin_schema import (
    AdminCreate,
    AdminResetPasswordResponse,
    AdminUpdate,
)


# Mật khẩu mặc định của tài khoản nhân viên mới
# hoặc sau khi chủ quán thực hiện reset.
DEFAULT_STAFF_PASSWORD = "abc12345"

# Sử dụng Argon2 giống cơ chế đăng nhập hiện tại.
password_hasher = PasswordHash.recommended()


class AdminManagementService:
    def _ensure_owner(
        self,
        current_admin: dict,
    ) -> None:
        """
        Chỉ chủ quán mới được sử dụng chức năng
        quản lý nhân sự.

        Kiểm tra này được thực hiện phía backend,
        nên STAFF không thể vượt qua bằng cách nhập URL.
        """
        if (
            current_admin is None
            or current_admin.get("role") != "OWNER"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Chỉ chủ quán mới được quyền "
                    "quản lý nhân sự"
                ),
            )

    def _get_staff_or_error(
        self,
        admin_id: int,
    ) -> dict:
        """
        Tìm tài khoản nhân viên và đảm bảo tài khoản đó
        không phải OWNER.
        """
        admin = admin_repository.get_by_id(
            admin_id
        )

        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản",
            )

        if admin["role"] == "OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Không thể sửa hoặc đặt lại mật khẩu "
                    "của tài khoản chủ quán"
                ),
            )

        return admin

    def get_all_admins(
        self,
        current_admin: dict,
        phone_keyword: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict]:
        """
        Lấy danh sách quản trị viên.

        Hỗ trợ:
        - Tìm kiếm gần đúng theo số điện thoại.
        - Lọc theo trạng thái hoạt động.
        """
        self._ensure_owner(current_admin)

        normalized_phone = None

        if phone_keyword:
            normalized_phone = (
                phone_keyword.strip()
            )

        return admin_repository.get_all(
            phone_keyword=normalized_phone,
            is_active=is_active,
        )

    def get_admin_by_id(
        self,
        admin_id: int,
        current_admin: dict,
    ) -> dict:
        """Lấy chi tiết một tài khoản quản trị viên."""
        self._ensure_owner(current_admin)

        admin = admin_repository.get_by_id(
            admin_id
        )

        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản",
            )

        return admin

    def create_staff(
        self,
        data: AdminCreate,
        current_admin: dict,
    ) -> dict:
        """
        Chủ quán cấp tài khoản mới cho nhân viên.

        Tài khoản mới luôn:
        - Có role STAFF.
        - Có trạng thái hoạt động.
        - Có mật khẩu mặc định abc12345.
        - Phải đổi mật khẩu sau lần đăng nhập đầu tiên.
        """
        self._ensure_owner(current_admin)

        staff_data = data.model_dump()

        # Chuẩn hóa dữ liệu trước khi kiểm tra và lưu.
        staff_data["username"] = (
            staff_data["username"]
            .strip()
            .lower()
        )

        staff_data["full_name"] = (
            staff_data["full_name"].strip()
        )

        staff_data["phone"] = (
            staff_data["phone"].strip()
        )

        staff_data["email"] = (
            staff_data["email"]
            .strip()
            .lower()
        )

        if not staff_data["full_name"]:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail="Họ và tên không được để trống",
            )

        # Kiểm tra username đã tồn tại.
        existing_username = (
            admin_repository.get_by_username(
                staff_data["username"]
            )
        )

        if existing_username is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên đăng nhập đã được sử dụng",
            )

        # Kiểm tra số điện thoại đã tồn tại.
        existing_phone = (
            admin_repository.get_by_phone(
                staff_data["phone"]
            )
        )

        if existing_phone is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Số điện thoại đã được sử dụng",
            )

        # Kiểm tra email đã tồn tại.
        existing_email = (
            admin_repository.get_by_email(
                staff_data["email"]
            )
        )

        if existing_email is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email đã được sử dụng",
            )

        # Không lưu abc12345 trực tiếp vào SQL.
        # Chỉ lưu chuỗi hash Argon2.
        default_password_hash = (
            password_hasher.hash(
                DEFAULT_STAFF_PASSWORD
            )
        )

        try:
            return admin_repository.create_staff(
                data=staff_data,
                password_hash=default_password_hash,
                created_by_admin_id=(
                    current_admin["id"]
                ),
            )

        except IntegrityError as error:
            # Phòng trường hợp hai request tạo tài khoản
            # trùng nhau gần như cùng một thời điểm.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Username, số điện thoại hoặc email "
                    "đã được sử dụng"
                ),
            ) from error

    def update_staff(
        self,
        admin_id: int,
        data: AdminUpdate,
        current_admin: dict,
    ) -> dict:
        """
        Sửa thông tin và trạng thái nhân viên.

        Trạng thái hoạt động được sửa tại đây,
        không có chức năng bật/tắt riêng.
        """
        self._ensure_owner(current_admin)

        existing_staff = (
            self._get_staff_or_error(admin_id)
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        # Không cho ghi NULL vào các thông tin nhân sự.
        update_data = {
            field: value
            for field, value in update_data.items()
            if value is not None
        }

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Không có thông tin nào để cập nhật"
                ),
            )

        if "full_name" in update_data:
            update_data["full_name"] = (
                update_data["full_name"].strip()
            )

            if not update_data["full_name"]:
                raise HTTPException(
                    status_code=(
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "Họ và tên không được để trống"
                    ),
                )

        if "phone" in update_data:
            update_data["phone"] = (
                update_data["phone"].strip()
            )

            duplicated_phone = (
                admin_repository.get_by_phone(
                    update_data["phone"]
                )
            )

            if (
                duplicated_phone is not None
                and duplicated_phone["id"]
                != existing_staff["id"]
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Số điện thoại đã được sử dụng"
                    ),
                )

        if "email" in update_data:
            update_data["email"] = (
                update_data["email"]
                .strip()
                .lower()
            )

            duplicated_email = (
                admin_repository.get_by_email(
                    update_data["email"]
                )
            )

            if (
                duplicated_email is not None
                and duplicated_email["id"]
                != existing_staff["id"]
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail="Email đã được sử dụng",
                )

        try:
            updated_staff = (
                admin_repository.update_staff(
                    admin_id=admin_id,
                    data=update_data,
                )
            )

        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Số điện thoại hoặc email "
                    "đã được sử dụng"
                ),
            ) from error

        if updated_staff is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy nhân viên",
            )

        return updated_staff

    def reset_staff_password(
        self,
        admin_id: int,
        current_admin: dict,
    ) -> AdminResetPasswordResponse:
        """
        Đưa mật khẩu nhân viên về abc12345.

        Đồng thời must_change_password được đặt thành 1.
        """
        self._ensure_owner(current_admin)
        self._get_staff_or_error(admin_id)

        default_password_hash = (
            password_hasher.hash(
                DEFAULT_STAFF_PASSWORD
            )
        )

        was_updated = (
            admin_repository.reset_staff_password(
                admin_id=admin_id,
                password_hash=default_password_hash,
            )
        )

        if not was_updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy nhân viên",
            )

        return AdminResetPasswordResponse(
            message=(
                "Đã đặt lại mật khẩu về abc12345"
            )
        )


admin_management_service = (
    AdminManagementService()
)
"""Nghiệp vụ quản lý tài khoản SHOP_OWNER trên database V2."""

from types import SimpleNamespace

from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from app.repositaries.people_repository import people_repository
from app.schemas.admin_schema import (
    ResetPasswordResponse,
    ShopOwnerCreate,
    ShopOwnerUpdate,
)


# Mật khẩu chỉ được dùng làm giá trị ban đầu hoặc khi SYSTEM_ADMIN reset.
# Database luôn lưu chuỗi hash, không lưu trực tiếp abc12345.
DEFAULT_SHOP_OWNER_PASSWORD = "abc12345"
password_hasher = PasswordHash.recommended()


class AdminManagementService:
    """Các nghiệp vụ nhân sự chỉ dành cho SYSTEM_ADMIN."""

    def _ensure_system_admin(self, current_admin: dict) -> None:
        """Kiểm tra lại vai trò ở service để bảo vệ nhiều lớp."""
        if (
            current_admin is None
            or current_admin.get("role") != "SYSTEM_ADMIN"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Chỉ quản trị hệ thống mới được quản lý "
                    "tài khoản chủ địa điểm"
                ),
            )

    def _get_shop_owner_or_error(self, person_id: int) -> dict:
        """Tìm đúng SHOP_OWNER, không cho tác động tài khoản vai trò khác."""
        person = people_repository.get_by_id(person_id)

        if person is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản",
            )

        if person["role"] != "SHOP_OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Chức năng này chỉ được tác động đến "
                    "tài khoản chủ địa điểm"
                ),
            )

        return person

    def get_all_shop_owners(
        self,
        current_admin: dict,
        phone_keyword: str | None = None,
        is_active: bool | None = None,
        keyword: str | None = None,
    ) -> list[dict]:
        """Lấy SHOP_OWNER, tìm theo tên quán/SĐT và lọc trạng thái."""
        self._ensure_system_admin(current_admin)

        # phone_keyword được giữ tạm để router cũ vẫn hoạt động.
        search_value = keyword or phone_keyword
        normalized_keyword = (
            search_value.strip() if search_value else None
        )

        return people_repository.get_all_shop_owners(
            keyword=normalized_keyword,
            is_active=is_active,
        )

    def get_shop_owner_by_id(
        self,
        admin_id: int,
        current_admin: dict,
    ) -> dict:
        """Lấy chi tiết một SHOP_OWNER theo ID trong bảng people."""
        self._ensure_system_admin(current_admin)
        return self._get_shop_owner_or_error(admin_id)

    def create_shop_owner(
        self,
        data: ShopOwnerCreate,
        current_admin: dict,
    ) -> dict:
        """SYSTEM_ADMIN cấp tài khoản SHOP_OWNER mới."""
        self._ensure_system_admin(current_admin)

        username = data.username.strip().lower()
        full_name = data.full_name.strip()
        phone = data.phone.strip() if data.phone else None
        email = data.email.strip().lower()

        if not username:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tên đăng nhập không được để trống",
            )

        if not full_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Họ và tên không được để trống",
            )

        if not email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email không được để trống",
            )

        # Username, số điện thoại và email là duy nhất trên toàn bảng people,
        # không chỉ riêng nhóm SHOP_OWNER.
        if people_repository.get_by_username(username) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên đăng nhập đã được sử dụng",
            )

        if (
            phone is not None
            and people_repository.get_by_phone(phone) is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Số điện thoại đã được sử dụng",
            )

        if people_repository.get_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email đã được sử dụng",
            )

        default_password_hash = password_hasher.hash(
            DEFAULT_SHOP_OWNER_PASSWORD
        )

        # Repository nhận object có thuộc tính; SimpleNamespace chứa dữ liệu
        # đã được chuẩn hóa mà không làm thay đổi request ban đầu.
        normalized_data = SimpleNamespace(
            username=username,
            full_name=full_name,
            phone=phone,
            email=email,
        )

        try:
            return people_repository.create_shop_owner(
                data=normalized_data,
                password_hash=default_password_hash,
                created_by_system_admin_id=current_admin["id"],
            )
        except IntegrityError as error:
            # Vẫn bắt lỗi UNIQUE từ SQL Server để phòng hai request tạo
            # dữ liệu trùng nhau tại cùng một thời điểm.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Tên đăng nhập, số điện thoại hoặc email "
                    "đã được sử dụng"
                ),
            ) from error

    def update_shop_owner(
        self,
        admin_id: int,
        data: ShopOwnerUpdate,
        current_admin: dict,
    ) -> dict:
        """Sửa thông tin và is_active trong cùng một chức năng."""
        self._ensure_system_admin(current_admin)
        existing = self._get_shop_owner_or_error(admin_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data = {
            field: value
            for field, value in update_data.items()
            if value is not None
        }

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không có thông tin nào để cập nhật",
            )

        if "full_name" in update_data:
            update_data["full_name"] = update_data["full_name"].strip()
            if not update_data["full_name"]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Họ và tên không được để trống",
                )

        if "phone" in update_data:
            update_data["phone"] = update_data["phone"].strip()
            duplicate_phone = people_repository.get_by_phone(
                update_data["phone"]
            )
            if (
                duplicate_phone is not None
                and duplicate_phone["id"] != existing["id"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Số điện thoại đã được sử dụng",
                )

        if "email" in update_data:
            update_data["email"] = update_data["email"].strip().lower()
            duplicate_email = people_repository.get_by_email(
                update_data["email"]
            )
            if (
                duplicate_email is not None
                and duplicate_email["id"] != existing["id"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email đã được sử dụng",
                )

        # Tên quán không được cập nhật ở đây vì nó chính là pois.name.
        # Repository chỉ nhận các trường thuộc bảng people. Những trường
        # frontend không gửi sẽ được giữ nguyên từ dữ liệu hiện có.
        merged_data = SimpleNamespace(
            full_name=update_data.get(
                "full_name",
                existing["full_name"],
            ),
            phone=update_data.get("phone", existing["phone"]),
            email=update_data.get("email", existing["email"]),
            is_active=update_data.get(
                "is_active",
                existing["is_active"],
            ),
        )

        try:
            updated = people_repository.update_shop_owner(
                person_id=admin_id,
                data=merged_data,
            )
        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Số điện thoại hoặc email đã được sử dụng",
            ) from error

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy chủ địa điểm",
            )

        return updated

    def reset_shop_owner_password(
        self,
        admin_id: int,
        current_admin: dict,
    ) -> ResetPasswordResponse:
        """Đặt mật khẩu về abc12345 và buộc đổi ở lần đăng nhập sau."""
        self._ensure_system_admin(current_admin)
        self._get_shop_owner_or_error(admin_id)

        default_password_hash = password_hasher.hash(
            DEFAULT_SHOP_OWNER_PASSWORD
        )

        was_updated = people_repository.reset_shop_owner_password(
            person_id=admin_id,
            password_hash=default_password_hash,
        )

        if not was_updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy chủ địa điểm",
            )

        return ResetPasswordResponse(
            message="Đã đặt lại mật khẩu về abc12345"
        )

    # Tên cũ được giữ tạm để frontend/router cũ chưa bị gãy.
    def get_all_admins(
        self,
        current_admin: dict,
        phone_keyword: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict]:
        return self.get_all_shop_owners(
            current_admin=current_admin,
            phone_keyword=phone_keyword,
            is_active=is_active,
        )

    def get_admin_by_id(self, admin_id: int, current_admin: dict) -> dict:
        return self.get_shop_owner_by_id(admin_id, current_admin)

    def create_staff(
        self,
        data: ShopOwnerCreate,
        current_admin: dict,
    ) -> dict:
        return self.create_shop_owner(data, current_admin)

    def update_staff(
        self,
        admin_id: int,
        data: ShopOwnerUpdate,
        current_admin: dict,
    ) -> dict:
        return self.update_shop_owner(admin_id, data, current_admin)

    def reset_staff_password(
        self,
        admin_id: int,
        current_admin: dict,
    ) -> ResetPasswordResponse:
        return self.reset_shop_owner_password(admin_id, current_admin)


admin_management_service = AdminManagementService()

"""Nghiệp vụ hồ sơ cá nhân dành riêng cho SHOP_OWNER."""

from types import SimpleNamespace

from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from app.repositaries.people_repository import people_repository
from app.schemas.profile_schema import (
    ChangePasswordRequest,
    ProfileMessageResponse,
    ShopOwnerProfileUpdate,
)


password_hasher = PasswordHash.recommended()


class ProfileService:
    """Đọc/sửa đúng tài khoản lấy từ JWT, không nhận person_id từ client."""

    @staticmethod
    def _ensure_shop_owner(current_person: dict) -> None:
        if current_person.get("role") != "SHOP_OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chức năng này chỉ dành cho chủ quán",
            )

    def _get_current_shop_owner(self, current_person: dict) -> dict:
        self._ensure_shop_owner(current_person)
        person = people_repository.get_by_id(current_person["id"])

        if person is None or person["role"] != "SHOP_OWNER":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản chủ quán",
            )

        return person

    def get_my_profile(self, current_person: dict) -> dict:
        """Trả hồ sơ của chính SHOP_OWNER đang đăng nhập."""
        return self._get_current_shop_owner(current_person)

    def update_my_profile(
        self,
        data: ShopOwnerProfileUpdate,
        current_person: dict,
    ) -> dict:
        """Sửa hồ sơ và bảo vệ tính duy nhất của SĐT/email."""
        existing = self._get_current_shop_owner(current_person)

        full_name = data.full_name.strip()
        phone = data.phone.strip()
        email = data.email.strip().lower()

        duplicate_phone = people_repository.get_by_phone(phone)
        if (
            duplicate_phone is not None
            and duplicate_phone["id"] != existing["id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Số điện thoại đã được sử dụng",
            )

        duplicate_email = people_repository.get_by_email(email)
        if (
            duplicate_email is not None
            and duplicate_email["id"] != existing["id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email đã được sử dụng",
            )

        normalized_data = SimpleNamespace(
            full_name=full_name,
            phone=phone,
            email=email,
        )

        try:
            updated = people_repository.update_own_profile(
                person_id=current_person["id"],
                data=normalized_data,
            )
        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Số điện thoại hoặc email đã được sử dụng",
            ) from error

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản chủ quán",
            )

        return updated

    def change_my_password(
        self,
        data: ChangePasswordRequest,
        current_person: dict,
    ) -> ProfileMessageResponse:
        """Kiểm tra mật khẩu cũ rồi băm mật khẩu mới trước khi lưu SQL."""
        person = self._get_current_shop_owner(current_person)

        if data.new_password != data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Xác nhận mật khẩu mới không khớp",
            )

        try:
            current_password_is_valid = password_hasher.verify(
                data.current_password,
                person["password_hash"],
            )
        except Exception:
            current_password_is_valid = False

        if current_password_is_valid is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không đúng",
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu mới phải khác mật khẩu hiện tại",
            )

        # Chỉ password_hash được gửi xuống repository; mật khẩu gốc không
        # bao giờ được ghi vào database hoặc trả lại frontend.
        new_password_hash = password_hasher.hash(data.new_password)
        was_updated = people_repository.update_own_password(
            person_id=current_person["id"],
            password_hash=new_password_hash,
        )

        if was_updated is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tài khoản chủ quán",
            )

        return ProfileMessageResponse(
            message="Đổi mật khẩu thành công. Vui lòng đăng nhập lại."
        )


profile_service = ProfileService()

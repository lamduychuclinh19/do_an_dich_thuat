"""Xử lý đăng nhập và JWT cho toàn bộ tài khoản trong bảng people."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from app.repositaries.people_repository import people_repository
from app.schemas.auth_schema import AdminLogin, TokenResponse


load_dotenv()

password_hash = PasswordHash.recommended()
JWT_ALGORITHM = "HS256"

# Chỉ ba vai trò này mới được chấp nhận trong JWT của hệ thống.
VALID_ROLES = {
    "SYSTEM_ADMIN",
    "SHOP_OWNER",
    "TOURIST",
}

# Nếu username không tồn tại, hệ thống vẫn kiểm tra với một hash giả.
# Việc này giúp hạn chế kẻ xấu đoán tài khoản qua thời gian phản hồi.
DUMMY_PASSWORD_HASH = password_hash.hash(
    "this-is-not-a-real-person-password"
)


def is_active_account(value: object) -> bool:
    """Quy đổi trạng thái SQL Server: 1 là hoạt động, 0 là bị khóa."""
    return value is True or value == 1 or value == "1"


class AuthService:
    """Đăng nhập, tạo JWT và xác thực người dùng hiện tại."""

    def _get_jwt_settings(self) -> tuple[str, int]:
        """Đọc khóa bí mật và thời hạn JWT từ file .env."""
        jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        expire_minutes_text = os.getenv(
            "JWT_EXPIRE_MINUTES",
            "60",
        )

        if not jwt_secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT chưa được cấu hình",
            )

        try:
            expire_minutes = int(expire_minutes_text)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT_EXPIRE_MINUTES phải là số nguyên",
            )

        if expire_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT_EXPIRE_MINUTES phải lớn hơn 0",
            )

        return jwt_secret_key, expire_minutes

    def login_person(
        self,
        login_data: AdminLogin,
    ) -> TokenResponse:
        """Đăng nhập chung cho SYSTEM_ADMIN, SHOP_OWNER và TOURIST."""
        person = people_repository.get_by_username(
            login_data.username.strip()
        )

        stored_password_hash = (
            person["password_hash"]
            if person is not None
            else DUMMY_PASSWORD_HASH
        )

        try:
            password_is_valid = password_hash.verify(
                login_data.password,
                stored_password_hash,
            )
        except Exception:
            # Một hash bị hỏng trong database cũng không được làm API lỗi 500.
            password_is_valid = False


        if person is None or password_is_valid is False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu không đúng",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if person["role"] not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản không có quyền truy cập hệ thống",
            )

        # Database lưu is_active bằng 0/1, không dùng `is False` vì
        # trong Python, số 0 và boolean False không phải cùng một object.
        if not is_active_account(person["is_active"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Tài khoản của bạn đã bị khóa. "
                    "Vui lòng liên hệ quản trị viên."
                ),
            )

        access_token = self._create_access_token(
            person_id=person["id"],
            username=person["username"],
            role=person["role"],
            must_change_password=person["must_change_password"],
        )

        people_repository.update_last_login(person["id"])

        return TokenResponse(access_token=access_token)

    # Giữ tên cũ để auth_router hiện tại vẫn chạy trong lúc chuyển sang V2.
    def login_admin(
        self,
        login_data: AdminLogin,
    ) -> TokenResponse:
        return self.login_person(login_data)

    def _create_access_token(
        self,
        person_id: int,
        username: str,
        role: str,
        must_change_password: bool,
    ) -> str:
        """Tạo token chứa đúng ID và vai trò lấy từ database."""
        jwt_secret_key, expire_minutes = self._get_jwt_settings()

        current_time = datetime.now(timezone.utc)
        expires_at = current_time + timedelta(
            minutes=expire_minutes
        )

        payload = {
            "sub": str(person_id),
            "username": username,
            "role": role,
            "must_change_password": must_change_password,
            "iat": current_time,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            jwt_secret_key,
            algorithm=JWT_ALGORITHM,
        )

    def verify_access_token(self, token: str) -> dict:
        """Giải mã JWT rồi đối chiếu lại tài khoản thật trong database."""
        jwt_secret_key, _ = self._get_jwt_settings()

        unauthorized_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                token,
                jwt_secret_key,
                algorithms=[JWT_ALGORITHM],
            )

            person_id_text = payload.get("sub")
            token_username = payload.get("username")
            token_role = payload.get("role")

            if (
                person_id_text is None
                or token_username is None
                or token_role not in VALID_ROLES
            ):
                raise unauthorized_exception

            person_id = int(person_id_text)

        except (
            jwt.InvalidTokenError,
            ValueError,
            TypeError,
        ):
            raise unauthorized_exception

        person = people_repository.get_by_id(person_id)

        # Không chỉ tin dữ liệu trong token: luôn kiểm tra lại database.
        # Vì vậy tài khoản vừa bị khóa sẽ mất quyền ngay ở request kế tiếp.
        if (
            person is None
             or not is_active_account(person["is_active"])
            or person["role"] not in VALID_ROLES
            or person["role"] != token_role
            or person["username"] != token_username
        ):
            raise unauthorized_exception

        return {
            "id": person["id"],
            "username": person["username"],
            "full_name": person["full_name"],
            "role": person["role"],
            "must_change_password": person[
                "must_change_password"
            ],
        }


auth_service = AuthService()

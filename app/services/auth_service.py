import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from app.repositaries.admin_repository import (
    admin_repository,
)
from app.schemas.auth_schema import (
    AdminLogin,
    TokenResponse,
)


load_dotenv()

password_hash = PasswordHash.recommended()

JWT_ALGORITHM = "HS256"

# Dùng để kiểm tra mật khẩu ngay cả khi username không tồn tại,
# giúp phản hồi đăng nhập có thời gian xử lý tương đối giống nhau.
DUMMY_PASSWORD_HASH = password_hash.hash(
    "this-is-not-a-real-admin-password"
)


class AuthService:
    def _get_jwt_settings(self) -> tuple[str, int]:
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

        return jwt_secret_key, expire_minutes

    def login_admin(
        self,
        login_data: AdminLogin,
    ) -> TokenResponse:
        admin = admin_repository.get_by_username(
            login_data.username
        )

        stored_password_hash = (
            admin["password_hash"]
            if admin is not None
            else DUMMY_PASSWORD_HASH
        )

        password_is_valid = password_hash.verify(
            login_data.password,
            stored_password_hash,
        )

        if (
            admin is None
            or admin["is_active"] is False
            or password_is_valid is False
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tên đăng nhập hoặc mật khẩu không đúng",
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        access_token = self._create_access_token(
            admin_id=admin["id"],
            username=admin["username"],
        )

        return TokenResponse(
            access_token=access_token
        )

    def _create_access_token(
        self,
        admin_id: int,
        username: str,
    ) -> str:
        jwt_secret_key, expire_minutes = (
            self._get_jwt_settings()
        )

        current_time = datetime.now(timezone.utc)
        expires_at = current_time + timedelta(
            minutes=expire_minutes
        )

        payload = {
            "sub": str(admin_id),
            "username": username,
            "role": "admin",
            "iat": current_time,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            jwt_secret_key,
            algorithm=JWT_ALGORITHM,
        )

    def verify_access_token(
        self,
        token: str,
    ) -> dict:
        jwt_secret_key, _ = (
            self._get_jwt_settings()
        )

        unauthorized_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

        try:
            payload = jwt.decode(
                token,
                jwt_secret_key,
                algorithms=[JWT_ALGORITHM],
            )

            admin_id_text = payload.get("sub")
            role = payload.get("role")

            if (
                admin_id_text is None
                or role != "admin"
            ):
                raise unauthorized_exception

            admin_id = int(admin_id_text)

        except (
            jwt.InvalidTokenError,
            ValueError,
            TypeError,
        ):
            raise unauthorized_exception

        admin = admin_repository.get_by_id(admin_id)

        if (
            admin is None
            or admin["is_active"] is False
        ):
            raise unauthorized_exception

        return {
            "id": admin["id"],
            "username": admin["username"],
            "role": "admin",
        }


auth_service = AuthService()
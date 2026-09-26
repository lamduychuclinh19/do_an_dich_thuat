import os

from dotenv import load_dotenv

from app.repositaries.admin_repository import (
    admin_repository,
)


load_dotenv()


def seed_admin() -> None:
    username = os.getenv("ADMIN_USERNAME")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH")

    if not username or not password_hash:
        raise RuntimeError(
            "Thiếu ADMIN_USERNAME hoặc "
            "ADMIN_PASSWORD_HASH trong file .env"
        )

    existing_admin = (
        admin_repository.get_by_username(username)
    )

    if existing_admin is not None:
        print(
            f"Admin '{username}' đã tồn tại, "
            "không tạo thêm."
        )
        return

    admin = admin_repository.create(
        username=username,
        password_hash=password_hash,
    )

    print(
        f"Đã tạo admin '{admin['username']}' "
        f"với id = {admin['id']}."
    )


if __name__ == "__main__":
    seed_admin()

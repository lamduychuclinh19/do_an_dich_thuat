# Tiện ích tương tác để tạo tài khoản quản trị đầu tiên trong cơ sở dữ liệu.
import re
from getpass import getpass

from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine


EXPECTED_DATABASE_NAME = "MuseumGuideDB_V2"
password_hasher = PasswordHash.recommended()


def read_account_information() -> dict:
    """Nhập và kiểm tra thông tin tài khoản từ terminal."""
    username = input("Tên đăng nhập: ").strip().lower()
    full_name = input("Họ và tên: ").strip()
    phone = input("Số điện thoại: ").strip()
    email = input("Email: ").strip().lower()

    if not re.fullmatch(r"[a-z0-9_.-]{3,50}", username):
        raise ValueError(
            "Username phải dài 3-50 ký tự và chỉ chứa "
            "chữ, số, dấu chấm, gạch dưới hoặc gạch ngang."
        )

    if not 2 <= len(full_name) <= 150:
        raise ValueError("Họ và tên phải dài 2-150 ký tự.")

    if not re.fullmatch(r"0[0-9]{9}", phone):
        raise ValueError(
            "Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng 0."
        )

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Email không đúng định dạng.")

    password = getpass("Mật khẩu: ")
    confirmed_password = getpass("Nhập lại mật khẩu: ")

    if len(password) < 8:
        raise ValueError("Mật khẩu phải có ít nhất 8 ký tự.")

    if password != confirmed_password:
        raise ValueError("Hai lần nhập mật khẩu không giống nhau.")

    return {
        "username": username,
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "password": password,
    }


def create_first_system_admin() -> None:
    """Băm mật khẩu và thêm SYSTEM_ADMIN đầu tiên vào bảng people."""
    account = read_account_information()

    # Database chỉ nhận chuỗi hash Argon2, không nhận mật khẩu gốc.
    generated_password_hash = password_hasher.hash(
        account["password"]
    )

    with engine.begin() as connection:
        current_database = connection.execute(
            text("SELECT DB_NAME()")
        ).scalar_one()

        # Ngăn script vô tình ghi dữ liệu vào database cũ.
        if current_database != EXPECTED_DATABASE_NAME:
            raise RuntimeError(
                "Backend đang kết nối tới "
                f"{current_database!r}, không phải "
                f"{EXPECTED_DATABASE_NAME!r}. Hãy kiểm tra lại .env."
            )

        people_table_exists = connection.execute(
            text("SELECT OBJECT_ID(N'dbo.people', N'U')")
        ).scalar_one_or_none()

        if people_table_exists is None:
            raise RuntimeError(
                "Không tìm thấy dbo.people. Hãy chạy file "
                "MuseumGuideDB_V2.sql trước."
            )

        existing_system_admin = connection.execute(
            text(
                """
                SELECT TOP (1) id, username
                FROM dbo.people
                WHERE role = 'SYSTEM_ADMIN'
                ORDER BY id
                """
            )
        ).mappings().first()

        # Script bootstrap chỉ được phép tạo tài khoản hệ thống đầu tiên.
        if existing_system_admin is not None:
            raise RuntimeError(
                "Database đã có SYSTEM_ADMIN: "
                f"{existing_system_admin['username']!r}. "
                "Không tạo thêm bằng script bootstrap."
            )

        # Không dùng OUTPUT ở đây. SQL Server không cho OUTPUT không có INTO
        # trên một bảng đang bật trigger như dbo.people.
        connection.execute(
            text(
                """
                INSERT INTO dbo.people
                (
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
                VALUES
                (
                    :username,
                    :password_hash,
                    :full_name,
                    :phone,
                    :email,
                    'SYSTEM_ADMIN',
                    1,
                    0,
                    NULL
                )
                """
            ),
            {
                "username": account["username"],
                "password_hash": generated_password_hash,
                "full_name": account["full_name"],
                "phone": account["phone"],
                "email": account["email"],
            },
        )

        # Đọc lại bằng username sau INSERT để lấy thông tin hiển thị.
        created_admin = connection.execute(
            text(
                """
                SELECT id, username, full_name, role
                FROM dbo.people
                WHERE username = :username
                """
            ),
            {"username": account["username"]},
        ).mappings().one()

    print()
    print("Tạo SYSTEM_ADMIN thành công.")
    print(f"ID: {created_admin['id']}")
    print(f"Username: {created_admin['username']}")
    print(f"Họ tên: {created_admin['full_name']}")
    print(f"Role: {created_admin['role']}")


if __name__ == "__main__":
    try:
        create_first_system_admin()
    except (ValueError, RuntimeError) as error:
        print(f"Không thể tạo SYSTEM_ADMIN: {error}")
    except IntegrityError:
        print(
            "Không thể tạo SYSTEM_ADMIN: username, email hoặc "
            "số điện thoại đã tồn tại."
        )

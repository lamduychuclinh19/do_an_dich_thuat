import os

import jwt
import pytest
from fastapi import HTTPException

from app.schemas.auth_schema import AdminLogin
from app.services.auth_service import JWT_ALGORITHM, auth_service


def login(username="admin01", password="Secret123"):
    return auth_service.login_admin(
        AdminLogin(username=username, password=password)
    )


def test_login_success_returns_bearer_token_and_updates_last_login(backend):
    admin = backend.add_admin(username="admin01", password="Secret123")

    result = login()

    payload = jwt.decode(
        result.access_token,
        os.environ["JWT_SECRET_KEY"],
        algorithms=[JWT_ALGORITHM],
    )
    assert result.token_type == "bearer"
    assert payload["sub"] == str(admin["id"])
    assert backend.admins[admin["id"]]["last_login_at"] is not None


@pytest.mark.parametrize(
    "username, password",
    [
        ("admin01", "SaiMatKhau1"),  # sai mật khẩu
        ("khongco", "Secret123"),    # username không tồn tại
    ],
)
def test_login_rejects_wrong_credentials(backend, username, password):
    backend.add_admin(username="admin01", password="Secret123")

    with pytest.raises(HTTPException) as error:
        login(username, password)

    assert error.value.status_code == 401
    assert all(a["last_login_at"] is None for a in backend.admins.values())


def test_login_rejects_inactive_admin(backend):
    backend.add_admin(username="admin01", password="Secret123", is_active=False)

    with pytest.raises(HTTPException) as error:
        login()

    assert error.value.status_code == 401


def test_verify_token_takes_role_from_database_not_from_token(backend):
    admin = backend.add_admin(role="STAFF")
    token = login().access_token

    current_admin = auth_service.verify_access_token(token)

    assert current_admin["id"] == admin["id"]
    assert current_admin["role"] == "STAFF"  # không phải "admin" trong token


def test_verify_token_rejects_expired_token(backend, monkeypatch):
    backend.add_admin()
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "-1")  # token hết hạn ngay
    token = login().access_token

    with pytest.raises(HTTPException) as error:
        auth_service.verify_access_token(token)

    assert error.value.status_code == 401


def test_verify_token_rejects_token_signed_with_another_key(backend):
    backend.add_admin()
    forged = jwt.encode(
        {"sub": "1", "role": "admin"},
        "khoa-gia-mao-khoa-gia-mao-khoa-gia-mao",
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(HTTPException) as error:
        auth_service.verify_access_token(forged)

    assert error.value.status_code == 401


def test_verify_token_rejects_wrong_role_claim(backend):
    backend.add_admin()
    token = jwt.encode(
        {"sub": "1", "role": "user"},
        os.environ["JWT_SECRET_KEY"],
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(HTTPException) as error:
        auth_service.verify_access_token(token)

    assert error.value.status_code == 401


def test_verify_token_rejects_garbage_string():
    with pytest.raises(HTTPException) as error:
        auth_service.verify_access_token("khong-phai-jwt")

    assert error.value.status_code == 401


def test_verify_token_rejects_admin_deactivated_after_login(backend):
    admin = backend.add_admin()
    token = login().access_token
    backend.admins[admin["id"]]["is_active"] = False

    with pytest.raises(HTTPException) as error:
        auth_service.verify_access_token(token)

    assert error.value.status_code == 401


def test_missing_jwt_secret_returns_500(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY")

    with pytest.raises(HTTPException) as error:
        auth_service.verify_access_token("bat-ky")

    assert error.value.status_code == 500


def test_non_numeric_expire_minutes_returns_500(monkeypatch):
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "abc")

    with pytest.raises(HTTPException) as error:
        auth_service.verify_access_token("bat-ky")

    assert error.value.status_code == 500

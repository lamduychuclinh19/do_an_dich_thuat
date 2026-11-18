import pytest

ADMIN_ENDPOINTS = [
    ("get", "/api/admin/pois"),
    ("post", "/api/admin/pois"),
    ("put", "/api/admin/pois/1"),
    ("patch", "/api/admin/pois/1/visibility"),
    ("get", "/api/admin/translations/poi/1"),
    ("post", "/api/admin/translations"),
    ("patch", "/api/admin/translations/1/visibility"),
]


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_success_returns_bearer_token(client, backend):
    backend.add_admin(username="admin01", password="Secret123")

    response = client.post(
        "/api/auth/login",
        json={"username": "admin01", "password": "Secret123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_wrong_password_returns_401(client, backend):
    backend.add_admin(username="admin01", password="Secret123")

    response = client.post(
        "/api/auth/login",
        json={"username": "admin01", "password": "SaiMatKhau1"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "password": "Secret123"},  # username quá ngắn
        {"username": "admin01", "password": "123"},   # password quá ngắn
        {"username": "admin01"},                      # thiếu password
    ],
)
def test_login_validates_payload(client, payload):
    assert client.post("/api/auth/login", json=payload).status_code == 422


@pytest.mark.parametrize("method, path", ADMIN_ENDPOINTS)
def test_admin_endpoints_require_a_token(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_admin_endpoint_rejects_invalid_token(client):
    response = client.get(
        "/api/admin/pois",
        headers={"Authorization": "Bearer khong-hop-le"},
    )

    assert response.status_code == 401


def test_admin_endpoint_accepts_valid_token(client, admin_headers):
    response = client.get("/api/admin/pois", headers=admin_headers)

    assert response.status_code == 200


def test_token_stops_working_when_account_is_deactivated(
    client, backend, admin_headers
):
    for admin in backend.admins.values():
        admin["is_active"] = False

    response = client.get("/api/admin/pois", headers=admin_headers)

    assert response.status_code == 401

"""Test luồng POI theo quy trình mới: chủ quán gửi yêu cầu -> admin duyệt.

Không cần SQL Server: toàn bộ repository được thay bằng bộ nhớ giả.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth_dependency import (
    require_back_office,
    require_system_admin,
)
from app.repositaries.content_request_repository import (
    content_request_repository,
)
from app.repositaries.poi_repository import poi_repository

client = TestClient(app)

OWNER = {"id": 1, "username": "test_owner", "role": "SHOP_OWNER"}
ADMIN = {"id": 99, "username": "test_admin", "role": "SYSTEM_ADMIN"}

POI_ID = "BNR01"


@pytest.fixture(autouse=True)
def mock_login():
    app.dependency_overrides[require_back_office] = lambda: OWNER
    app.dependency_overrides[require_system_admin] = lambda: ADMIN
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_repositories(monkeypatch):
    pois: dict[str, dict] = {}
    requests: dict[int, dict] = {}

    # ---------- poi_repository ----------
    def create(data, owner_id, poi_id):
        poi = {**data, "id": poi_id, "owner_id": owner_id, "is_active": True}
        pois[poi_id] = poi
        return poi

    def get_by_id(poi_id):
        return pois.get(poi_id)

    def get_by_id_for_owner(poi_id, owner_id):
        poi = pois.get(poi_id)
        return poi if poi and poi["owner_id"] == owner_id else None

    def update(poi_id, owner_id, data):
        poi = get_by_id_for_owner(poi_id, owner_id)
        if poi is None:
            return None
        poi.update(data)
        return poi

    def set_visibility(poi_id, owner_id, is_active):
        poi = get_by_id_for_owner(poi_id, owner_id)
        if poi is None:
            return None
        poi["is_active"] = is_active
        return poi

    def get_active():
        return [p for p in pois.values() if p["is_active"]]

    def get_all_for_owner(owner_id):
        return [p for p in pois.values() if p["owner_id"] == owner_id]

    for name, fn in {
        "create": create,
        "get_by_id": get_by_id,
        "get_by_id_for_owner": get_by_id_for_owner,
        "update": update,
        "set_visibility": set_visibility,
        "get_active": get_active,
        "get_all_for_owner": get_all_for_owner,
    }.items():
        monkeypatch.setattr(poi_repository, name, fn)

    # ---------- content_request_repository ----------
    def has_pending(request_type, key):
        return any(
            r["request_type"] == request_type
            and r["status"] in ("PENDING", "PROCESSING")
            and r["details"].get("requested_poi_id") == key
            for r in requests.values()
        )

    def cr_create(*, request_type, action, submitter_id, details):
        request_id = len(requests) + 1
        item = {
            "id": request_id,
            "request_type": request_type,
            "action": action,
            "submitted_by_person_id": submitter_id,
            "status": "PENDING",
            "details": dict(details),
        }
        requests[request_id] = item
        return item

    def claim(request_id):
        item = requests.get(request_id)
        if item is None or item["status"] != "PENDING":
            return None
        item["status"] = "PROCESSING"
        return item

    def finalize(request, admin_id, approved, note):
        requests[request["id"]]["status"] = (
            "APPROVED" if approved else "REJECTED"
        )

    def release(request_id):
        requests[request_id]["status"] = "PENDING"

    for name, fn in {
        "has_pending": has_pending,
        "create": cr_create,
        "claim": claim,
        "finalize": finalize,
        "release": release,
    }.items():
        monkeypatch.setattr(content_request_repository, name, fn)


def poi_payload(**overrides):
    payload = {
        "id": POI_ID,
        "name": "Điểm trưng bày A",
        "description": "Nội dung thuyết minh của điểm A",
        "address": "Bảo tàng",
        "latitude": 10.776900,
        "longitude": 106.700900,
        "trigger_radius_meters": 2,
    }
    payload.update(overrides)
    return payload


def approve(request_id: int):
    response = client.post(
        f"/api/content-requests/admin/{request_id}/decision",
        json={"approved": True, "admin_note": "Đồng ý"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_poi_full_flow():
    # 1. Chủ quán gửi yêu cầu tạo POI -> chưa có POI công khai
    create_response = client.post("/api/admin/pois", json=poi_payload())
    assert create_response.status_code == 200
    request = create_response.json()
    assert request["status"] == "PENDING"
    assert request["details"]["requested_poi_id"] == POI_ID

    assert client.get(f"/api/public/pois/{POI_ID}").status_code == 404

    # 2. Admin duyệt -> POI xuất hiện
    approve(request["id"])

    get_response = client.get(f"/api/public/pois/{POI_ID}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == POI_ID
    assert get_response.json()["is_active"] is True

    # 3. Chủ quán gửi yêu cầu cập nhật, admin duyệt
    updated = poi_payload(name="Điểm trưng bày A đã cập nhật")
    updated.pop("id")
    update_response = client.put(f"/api/admin/pois/{POI_ID}", json=updated)
    assert update_response.status_code == 200
    approve(update_response.json()["id"])

    assert (
        client.get(f"/api/public/pois/{POI_ID}").json()["name"]
        == updated["name"]
    )

    # 4. Ẩn địa điểm
    hide_response = client.patch(
        f"/api/admin/pois/{POI_ID}/visibility", json={"is_active": False}
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["is_active"] is False

    # 5. POI ẩn không xem được công khai, chủ quán vẫn thấy
    assert client.get(f"/api/public/pois/{POI_ID}").status_code == 404
    public_list = client.get("/api/public/pois")
    assert public_list.status_code == 200
    assert all(p["id"] != POI_ID for p in public_list.json())

    owner_list = client.get("/api/admin/pois")
    assert owner_list.status_code == 200
    assert any(
        p["id"] == POI_ID and p["is_active"] is False
        for p in owner_list.json()
    )

    # 6. Hiện lại
    show_response = client.patch(
        f"/api/admin/pois/{POI_ID}/visibility", json={"is_active": True}
    )
    assert show_response.status_code == 200
    assert show_response.json()["is_active"] is True
    assert client.get(f"/api/public/pois/{POI_ID}").status_code == 200


def test_create_poi_requires_code():
    payload = poi_payload()
    payload.pop("id")
    assert client.post("/api/admin/pois", json=payload).status_code == 422


def test_system_admin_cannot_submit_poi_request():
    app.dependency_overrides[require_back_office] = lambda: ADMIN
    response = client.post("/api/admin/pois", json=poi_payload())
    assert response.status_code == 403
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth_dependency import require_back_office
from app.repositaries.poi_repository import poi_repository

client = TestClient(app)

OWNER = {"id": 1, "username": "test_owner", "role": "SHOP_OWNER"}
POI_ID = "BNR01"


@pytest.fixture(autouse=True)
def mock_login():
    app.dependency_overrides[require_back_office] = lambda: OWNER
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_poi_repository(monkeypatch):
    pois = {}

    def create(data, owner_id, poi_id):
        poi = {**data, "id": poi_id, "owner_id": owner_id, "is_active": True}
        pois[poi_id] = poi
        return poi

    def get_by_id(poi_id):
        return pois.get(poi_id)

    def update(poi_id, owner_id, data):
        poi = pois.get(poi_id)
        if poi is None or poi["owner_id"] != owner_id:
            return None
        poi.update(data)
        return poi

    def set_visibility(poi_id, owner_id, is_active):
        poi = pois.get(poi_id)
        if poi is None or poi["owner_id"] != owner_id:
            return None
        poi["is_active"] = is_active
        return poi

    def get_active():
        return [p for p in pois.values() if p["is_active"]]

    def get_all_for_owner(owner_id):
        return [p for p in pois.values() if p["owner_id"] == owner_id]

    monkeypatch.setattr(poi_repository, "create", create)
    monkeypatch.setattr(poi_repository, "get_by_id", get_by_id)
    monkeypatch.setattr(poi_repository, "update", update)
    monkeypatch.setattr(poi_repository, "set_visibility", set_visibility)
    monkeypatch.setattr(poi_repository, "get_active", get_active)
    monkeypatch.setattr(poi_repository, "get_all_for_owner", get_all_for_owner)


def test_poi_full_flow():
    # 1. Tạo địa điểm
    new_poi = {
        "id": POI_ID,
        "name": "Điểm trưng bày A",
        "description": "Nội dung thuyết minh của điểm A",
        "address": "Bảo tàng",
        "latitude": 10.776900,
        "longitude": 106.700900,
        "trigger_radius_meters": 2,
    }

    create_response = client.post("/api/admin/pois", json=new_poi)
    assert create_response.status_code == 201

    created_poi = create_response.json()
    assert created_poi["id"] == POI_ID
    assert created_poi["name"] == new_poi["name"]
    assert created_poi["is_active"] is True

    # 2. Lấy địa điểm theo id
    get_response = client.get(f"/api/public/pois/{POI_ID}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == POI_ID

    # 3. Cập nhật địa điểm
    updated_data = {
        "name": "Điểm trưng bày A đã cập nhật",
        "description": "Nội dung thuyết minh đã cập nhật",
        "address": "Bảo tàng",
        "latitude": 10.776900,
        "longitude": 106.700900,
        "trigger_radius_meters": 2,
    }
    update_response = client.put(f"/api/admin/pois/{POI_ID}", json=updated_data)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == updated_data["name"]

    # 4. Ẩn địa điểm
    hide_response = client.patch(
        f"/api/admin/pois/{POI_ID}/visibility", json={"is_active": False}
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["is_active"] is False

    # 5. Địa điểm ẩn không xem được công khai
    assert client.get(f"/api/public/pois/{POI_ID}").status_code == 404

    list_response = client.get("/api/public/pois")
    assert list_response.status_code == 200
    assert all(p["id"] != POI_ID for p in list_response.json())

    # Chủ quán vẫn xem được địa điểm đang ẩn
    owner_list = client.get("/api/admin/pois")
    assert owner_list.status_code == 200
    assert any(
        p["id"] == POI_ID and p["is_active"] is False
        for p in owner_list.json()
    )

    # 6. Hiện lại địa điểm
    show_response = client.patch(
        f"/api/admin/pois/{POI_ID}/visibility", json={"is_active": True}
    )
    assert show_response.status_code == 200
    assert show_response.json()["is_active"] is True
    assert client.get(f"/api/public/pois/{POI_ID}").status_code == 200
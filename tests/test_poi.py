import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositaries.poi_repository import poi_repository
from app.dependencies.auth_dependency import require_admin

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_admin_login():
    app.dependency_overrides[require_admin] = lambda: {
        "id": 1,
        "username": "test_admin",
        "role": "admin",
    }

    yield

    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_poi_repository(monkeypatch):
    pois = {}
    next_id = {"value": 1}

    def fake_create(data: dict):
        poi_id = next_id["value"]

        poi = {
            **data,
            "id": poi_id,
            "is_active": True,
        }

        pois[poi_id] = poi
        next_id["value"] += 1
        return poi

    def fake_get_by_id(poi_id: int):
        return pois.get(poi_id)

    def fake_get_active():
        return [
            poi
            for poi in pois.values()
            if poi["is_active"] is True
        ]

    def fake_get_all():
        return list(pois.values())

    def fake_update(poi_id: int, data: dict):
        poi = pois.get(poi_id)

        if poi is None:
            return None

        poi.update(data)
        return poi

    def fake_set_visibility(poi_id: int, is_active: bool):
        poi = pois.get(poi_id)

        if poi is None:
            return None

        poi["is_active"] = is_active
        return poi

    monkeypatch.setattr(
        poi_repository,
        "create",
        fake_create,
    )
    monkeypatch.setattr(
        poi_repository,
        "get_by_id",
        fake_get_by_id,
    )
    monkeypatch.setattr(
        poi_repository,
        "get_active",
        fake_get_active,
        raising=False,
    )
    monkeypatch.setattr(
        poi_repository,
        "get_all_active",
        fake_get_active,
        raising=False,
    )
    monkeypatch.setattr(
        poi_repository,
        "get_all",
        fake_get_all,
        raising=False,
    )
    monkeypatch.setattr(
        poi_repository,
        "update",
        fake_update,
    )
    monkeypatch.setattr(
        poi_repository,
        "set_visibility",
        fake_set_visibility,
    )
    
def test_poi_full_flow():
    # 1. Tạo địa điểm
    new_poi = {
    "name": "Điểm trưng bày A",
    "description": "Nội dung thuyết minh của điểm A",
    "address": "Bảo tàng",
    "latitude": 10.776900,
    "longitude": 106.700900,
    "trigger_radius_meters": 2
    }

    create_response = client.post("/api/pois", json=new_poi)

    assert create_response.status_code == 201

    created_poi = create_response.json()
    poi_id = created_poi["id"]

    assert created_poi["name"] == new_poi["name"]
    assert created_poi["is_active"] is True

    # 2. Lấy địa điểm theo id
    get_response = client.get(f"/api/pois/{poi_id}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == poi_id

    # 3. Cập nhật địa điểm
    updated_data = {
    "name": "Điểm trưng bày A đã cập nhật",
    "description": "Nội dung thuyết minh đã cập nhật",
    "address": "Bảo tàng",
    "latitude": 10.776900,
    "longitude": 106.700900,
    "trigger_radius_meters": 2
    }

    update_response = client.put(
        f"/api/pois/{poi_id}",
        json=updated_data
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == updated_data["name"]

    # 4. Ẩn địa điểm
    hide_response = client.patch(
        f"/api/pois/{poi_id}/visibility",
        json={"is_active": False}
    )

    assert hide_response.status_code == 200
    assert hide_response.json()["is_active"] is False

    # 5. Địa điểm ẩn không thể được xem công khai
    hidden_response = client.get(f"/api/pois/{poi_id}")

    assert hidden_response.status_code == 404

    list_response = client.get("/api/pois")

    assert list_response.status_code == 200
    assert all(
        poi["id"] != poi_id
        for poi in list_response.json()
    )

    # 6. Hiện lại địa điểm
    show_response = client.patch(
        f"/api/pois/{poi_id}/visibility",
        json={"is_active": True}
    )

    assert show_response.status_code == 200
    assert show_response.json()["is_active"] is True

    visible_response = client.get(f"/api/pois/{poi_id}")

    assert visible_response.status_code == 200

    # Khách đứng cách POI khoảng 1 mét
    nearby_response = client.get(
        "/api/pois/nearby",
        params={
            "latitude": 10.776909,
            "longitude": 106.700900
        }
    )

    assert nearby_response.status_code == 200

    nearby_poi = nearby_response.json()

    assert nearby_poi is not None
    assert nearby_poi["id"] == poi_id
    assert nearby_poi["distance_meters"] <= 2


    # Khách đứng cách POI khoảng 3 mét
    outside_response = client.get(
        "/api/pois/nearby",
        params={
            "latitude": 10.776927,
            "longitude": 106.700900
        }
    )

    assert outside_response.status_code == 200
    assert outside_response.json() is None
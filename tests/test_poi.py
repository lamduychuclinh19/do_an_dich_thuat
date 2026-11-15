from app.routers.admin_poi_router import create_poi
from app.schemas.poi_schema import BackOfficePoiCreate
from app.services.content_request_service import content_request_service


def test_shop_owner_submits_poi_creation_request(monkeypatch):
    submitted = {}

    def fake_submit(data, owner):
        submitted["data"] = data
        submitted["owner"] = owner
        return {"id": 1, "request_type": data.request_type, "status": "PENDING"}

    monkeypatch.setattr(content_request_service, "submit", fake_submit)

    response = create_poi(
        BackOfficePoiCreate(
            id="TEST1",
            name="Điểm trưng bày A",
            description="Nội dung thuyết minh của điểm A",
            address="Bảo tàng",
            latitude=10.7769,
            longitude=106.7009,
            trigger_radius_meters=30,
        ),
        {"id": 1, "username": "test_owner", "role": "SHOP_OWNER"},
    )

    assert response == {"id": 1, "request_type": "POI", "status": "PENDING"}
    assert submitted["data"].request_type == "POI"
    assert submitted["data"].action == "CREATE"
    assert submitted["data"].details["id"] == "TEST1"
    assert submitted["owner"]["id"] == 1

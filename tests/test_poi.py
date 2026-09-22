from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_and_get_poi():
    new_poi = {
        "name": "Bến Nhà Rồng",
        "description": "Một địa điểm lịch sử tại Quận 4",
        "address": "01 Nguyễn Tất Thành, Quận 4"
    }

    create_response = client.post("/api/pois", json=new_poi)

    assert create_response.status_code == 201

    created_poi = create_response.json()
    assert created_poi["name"] == new_poi["name"]
    assert created_poi["id"] == 1

    get_response = client.get("/api/pois")

    assert get_response.status_code == 200
    assert created_poi in get_response.json()
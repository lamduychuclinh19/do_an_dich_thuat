from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_poi_full_flow():
    # 1. Tạo địa điểm
    new_poi = {
        "name": "Bến Nhà Rồng",
        "description": "Một địa điểm lịch sử tại Quận 4",
        "address": "01 Nguyễn Tất Thành, Quận 4"
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
        "name": "Bảo tàng Hồ Chí Minh",
        "description": "Địa điểm tham quan lịch sử",
        "address": "01 Nguyễn Tất Thành, Quận 4"
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
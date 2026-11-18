import pytest

VALID_POI = {
    "name": "Điểm trưng bày A",
    "description": "Nội dung mô tả",
    "address": "Bảo tàng",
    "latitude": 10.7769,
    "longitude": 106.7009,
    "trigger_radius_meters": 2,
}


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", ""),
        ("description", ""),
        ("address", ""),
        ("latitude", 91),
        ("latitude", -91),
        ("longitude", 181),
        ("longitude", -181),
        # PoiCreate hiện chỉ cho phép bán kính 1–2 m. Nếu đổi giới hạn
        # trong app/schemas/poi_schema.py thì sửa hai dòng dưới đây.
        ("trigger_radius_meters", 0.5),
        ("trigger_radius_meters", 3),
    ],
)
def test_create_poi_rejects_invalid_values(client, admin_headers, field, value):
    response = client.post(
        "/api/admin/pois",
        json={**VALID_POI, field: value},
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_create_poi_accepts_boundary_values(client, admin_headers):
    payload = {
        **VALID_POI,
        "latitude": 90,
        "longitude": -180,
        "trigger_radius_meters": 1,
    }

    response = client.post("/api/admin/pois", json=payload, headers=admin_headers)

    assert response.status_code == 201


def test_update_unknown_poi_returns_404(client, admin_headers):
    response = client.put(
        "/api/admin/pois/999", json=VALID_POI, headers=admin_headers
    )

    assert response.status_code == 404


def test_hide_unknown_poi_returns_404(client, admin_headers):
    response = client.patch(
        "/api/admin/pois/999/visibility",
        json={"is_active": False},
        headers=admin_headers,
    )

    assert response.status_code == 404

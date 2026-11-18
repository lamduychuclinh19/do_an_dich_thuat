import pytest


def test_load_all_returns_empty_list_when_nothing_is_published(client):
    response = client.get(
        "/api/public/guide/load-all", params={"language_code": "vi"}
    )

    assert response.status_code == 200
    assert response.json() == []


def test_load_all_response_matches_schema(client, backend):
    poi = backend.add_poi(name="Điểm A")
    translation = backend.add_translation(
        poi["id"], "vi", title="Giới thiệu", narration_text="Xin chào"
    )

    response = client.get(
        "/api/public/guide/load-all", params={"language_code": "vi"}
    )

    assert response.status_code == 200
    [item] = response.json()
    assert item["poi_id"] == poi["id"]
    assert item["title"] == "Giới thiệu"
    assert item["audio_url"] == translation["audio_url"]
    assert item["is_fallback"] is False


def test_load_all_rejects_unknown_language(client):
    response = client.get(
        "/api/public/guide/load-all", params={"language_code": "xx"}
    )

    assert response.status_code == 422


def test_nearby_returns_guide_when_visitor_is_inside_radius(client, backend):
    poi = backend.add_poi(latitude=10.0, longitude=106.0)
    backend.add_translation(
        poi["id"], "vi", title="Tiêu đề VI", narration_text="Nội dung VI"
    )

    response = client.get(
        "/api/public/guide/nearby",
        params={
            "latitude": 10.00001,  # ≈ 1,1 m cách điểm
            "longitude": 106.0,
            "language_code": "vi",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["poi_id"] == poi["id"]
    assert body["title"] == "Tiêu đề VI"
    assert 0 < body["distance_meters"] <= 2


def test_nearby_returns_null_when_visitor_is_outside_radius(client, backend):
    poi = backend.add_poi(latitude=10.0, longitude=106.0)
    backend.add_translation(poi["id"], "vi")

    response = client.get(
        "/api/public/guide/nearby",
        params={"latitude": 10.001, "longitude": 106.0, "language_code": "vi"},
    )

    assert response.status_code == 200
    assert response.json() is None


def test_nearby_returns_404_when_language_is_missing(client, backend):
    # README ghi "trả null nếu chưa có bản dịch", nhưng code hiện trả 404.
    # Test này khóa hành vi thực tế; nếu đổi code thì sửa test (hoặc README).
    poi = backend.add_poi(latitude=10.0, longitude=106.0)
    backend.add_translation(poi["id"], "vi")

    response = client.get(
        "/api/public/guide/nearby",
        params={"latitude": 10.0, "longitude": 106.0, "language_code": "en"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"latitude": 91, "longitude": 106, "language_code": "vi"},
        {"latitude": 10, "longitude": 181, "language_code": "vi"},
        {"latitude": 10, "longitude": 106, "language_code": "xx"},
        {"latitude": 10, "longitude": 106},  # thiếu language_code
    ],
)
def test_nearby_validates_query_parameters(client, params):
    response = client.get("/api/public/guide/nearby", params=params)

    assert response.status_code == 422

import pytest

from app.services.poi_service import poi_service

# 0,00001 độ vĩ độ ≈ 1,11 m (đã kiểm tra bằng công thức Haversine)
STEP_1M = 0.00001


def test_distance_between_same_point_is_zero():
    assert poi_service.calculate_distance(10.0, 106.0, 10.0, 106.0) == 0


def test_distance_one_degree_of_latitude():
    distance = poi_service.calculate_distance(10.0, 106.0, 11.0, 106.0)

    assert distance == pytest.approx(111_195, rel=1e-3)


def test_distance_is_symmetric():
    a_to_b = poi_service.calculate_distance(10.7769, 106.7009, 10.78, 106.705)
    b_to_a = poi_service.calculate_distance(10.78, 106.705, 10.7769, 106.7009)

    assert a_to_b == pytest.approx(b_to_a)


def test_find_nearby_poi_inside_radius(backend):
    poi = backend.add_poi(latitude=10.0, longitude=106.0)

    result = poi_service.find_nearby_poi(10.0 + STEP_1M, 106.0)

    assert result is not None
    assert result["id"] == poi["id"]
    assert result["distance_meters"] == pytest.approx(1.11, abs=0.05)


def test_find_nearby_poi_outside_radius_returns_none(backend):
    backend.add_poi(latitude=10.0, longitude=106.0)

    # 0,0001 độ ≈ 11 m, xa hơn bán kính 2 m
    assert poi_service.find_nearby_poi(10.0001, 106.0) is None


def test_find_nearby_poi_ignores_hidden_poi(backend):
    poi = backend.add_poi(latitude=10.0, longitude=106.0)
    backend.pois[poi["id"]]["is_active"] = False

    assert poi_service.find_nearby_poi(10.0, 106.0) is None


def test_find_nearby_poi_returns_the_closest_one(backend):
    backend.add_poi(name="Xa hơn", latitude=10.00001, longitude=106.0)
    near = backend.add_poi(name="Gần hơn", latitude=10.000005, longitude=106.0)

    result = poi_service.find_nearby_poi(10.0, 106.0)

    assert result["id"] == near["id"]

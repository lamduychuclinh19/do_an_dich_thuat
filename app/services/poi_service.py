from fastapi import HTTPException, status

from app.repositaries.poi_repository import poi_repository
from app.schemas.poi_schema import PoiCreate, PoiVisibility
from math import atan2, cos, radians, sin, sqrt


class PoiService:
    def create_poi(self, data: PoiCreate) -> dict:
        poi_data = data.model_dump()
        return poi_repository.create(poi_data)
    """
    Nó gọi Repository để tìm dữ liệu:
    Tìm thấy → trả địa điểm về.
    Không tìm thấy → trả lỗi HTTP 404 Not Found.
    """
    def get_poi_by_id(self, poi_id: int) -> dict:
        poi = poi_repository.get_by_id(poi_id)

        if poi is None or poi["is_active"] is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found"
            )

        return poi

    
    def update_poi(self, poi_id: int, data: PoiCreate) -> dict:
        poi_data = data.model_dump()
        updated_poi = poi_repository.update(poi_id, poi_data)

        if updated_poi is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found"
            )

        return updated_poi

    def set_poi_visibility(self,poi_id: int,data: PoiVisibility) -> dict:
        updated_poi = poi_repository.set_visibility(
            poi_id,
            data.is_active
        )

        if updated_poi is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="POI not found"
            )

        return updated_poi

    def get_all_pois(self) -> list:
        return poi_repository.get_active()

    def calculate_distance(
        self,
        user_latitude: float,
        user_longitude: float,
        poi_latitude: float,
        poi_longitude: float
    ) -> float:
        earth_radius = 6_371_000

        user_lat = radians(user_latitude)
        user_lng = radians(user_longitude)
        poi_lat = radians(poi_latitude)
        poi_lng = radians(poi_longitude)

        difference_lat = poi_lat - user_lat
        difference_lng = poi_lng - user_lng

        a = (
            sin(difference_lat / 2) ** 2
            + cos(user_lat)
            * cos(poi_lat)
            * sin(difference_lng / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earth_radius * c

    def find_nearby_poi(
        self,
        # vĩ độ
        latitude: float,
        # kinh độ
        longitude: float
    ) -> dict | None:
        nearest_poi = None

        for poi in poi_repository.get_active():
            distance = self.calculate_distance(
                latitude,
                longitude,
                poi["latitude"],
                poi["longitude"]
            )

            is_inside_trigger_area = (
                distance <= poi["trigger_radius_meters"]
            )

            if is_inside_trigger_area:
                if (
                    nearest_poi is None
                    or distance < nearest_poi["distance_meters"]
                ):
                    nearest_poi = {
                        **poi,
                        "distance_meters": round(distance, 2)
                    }

        return nearest_poi


poi_service = PoiService()
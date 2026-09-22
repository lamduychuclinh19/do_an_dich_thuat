from fastapi import HTTPException, status

from app.repositaries.poi_repository import poi_repository
from app.schemas.poi_schema import PoiCreate, PoiVisibility



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


poi_service = PoiService()
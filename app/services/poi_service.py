from app.repositaries.poi_repository import poi_repository
from app.schemas.poi_schema import PoiCreate


class PoiService:
    def create_poi(self, data: PoiCreate) -> dict:
        poi_data = data.model_dump()
        return poi_repository.create(poi_data)

    def get_all_pois(self) -> list:
        return poi_repository.get_all()


poi_service = PoiService()